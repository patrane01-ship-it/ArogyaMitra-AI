"""
ArogyaMitra AI - Health Records Router
Handles file upload, manual entry, retrieval, metadata updates, and in-memory decrypted downloads.
Per PRODUCTION_BACKEND.md §8.2, §9.2, §10.2.
"""

import os
import io
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from backend.config import settings, MAX_FILE_SIZE_MB, ALLOWED_MIME_TYPES
from backend.core.logger import logger
from backend.core.cache import ArogyaCache
from backend.core.dependencies import (
    get_current_user,
    get_record_repo,
    get_param_repo,
    get_cache,
    get_encryption_service,
)
from backend.models.health_record import HealthRecord, RecordType
from backend.models.clinical_parameter import ClinicalParameter
from backend.repositories.health_record_repo import HealthRecordRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.services.encryption_service import EncryptionService
from backend.agents.graph import run_pipeline
from backend.schemas.health_record_schema import (
    HealthRecordResponse,
    HealthRecordUploadResponse,
    HealthRecordUpdate,
    HealthRecordManualCreate,
)
from backend.exceptions.arogya_errors import (
    FileSizeLimitError,
    UnsupportedFileTypeError,
    RecordNotFoundError,
    ArogyaError,
)

router = APIRouter(prefix="/api/records", tags=["Records"])


async def validate_file_upload(file: UploadFile) -> bytes:
    """Validate MIME type, size limit, and PDF headers."""
    content = await file.read()
    
    # 1. Size check
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise FileSizeLimitError(f"File exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB")

    # 2. Content type validation
    content_type = file.content_type or ""
    # Try magic bytes or extension fallback
    if content.startswith(b"%PDF"):
        mime = "application/pdf"
    elif content.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif content.startswith(b"\x89PNG"):
        mime = "image/png"
    else:
        mime = content_type

    if mime not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileTypeError(f"Unsupported file format: {mime}. Allowed: PDF, JPG, PNG.")

    return content


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=HealthRecordUploadResponse,
)
async def upload_record(
    file: UploadFile = File(...),
    record_type: str = Form(default="LAB_REPORT"),
    report_date: Optional[str] = Form(default=None),
    user_id: str = Depends(get_current_user),
    record_repo: HealthRecordRepository = Depends(get_record_repo),
    encryption_svc: EncryptionService = Depends(get_encryption_service),
    cache: ArogyaCache = Depends(get_cache),
):
    """
    Upload a medical document:
    - Validates MIME and size
    - Encrypts via AES-256-GCM before writing to disk
    - Creates record in DB with is_processed=False
    - Returns 202 Accepted immediately
    - Spawns background agent pipeline
    """
    content_bytes = await validate_file_upload(file)

    parsed_date = datetime.now(timezone.utc)
    if report_date:
        try:
            parsed_date = datetime.fromisoformat(report_date)
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        except ValueError:
            parsed_date = datetime.now(timezone.utc)

    # 1. Encrypt payload
    encrypted_payload = encryption_svc.encrypt_to_payload(content_bytes)

    # 2. Prepare file path
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    temp_record = HealthRecord(
        user_id=user_id,
        record_type=record_type,
        report_date=parsed_date,
        is_processed=False,
    )
    temp_record.validate()
    file_path = os.path.join(settings.UPLOAD_DIR, f"{temp_record.record_id}.enc")
    temp_record.source_file_path = file_path

    # Write encrypted file
    with open(file_path, "wb") as f:
        f.write(encrypted_payload)

    # 3. Create DB record
    created = await record_repo.create(temp_record)

    # 4. Invalidate relevant user caches
    await cache.invalidate("clinical_params", user_id)
    await cache.invalidate("risk_score", user_id)

    # 5. Spawn background processing task
    asyncio.create_task(
        run_pipeline(
            record_id=created.record_id,
            user_id=user_id,
            file_path=file_path,
            record_type=record_type,
        )
    )

    logger.info(f"[RecordsRouter] Record {created.record_id} queued for processing")
    return {
        "record_id": created.record_id,
        "status": "processing",
        "message": "Document uploaded and encrypted. Analysis started.",
    }


@router.post("/manual", status_code=status.HTTP_201_CREATED, response_model=HealthRecordResponse)
async def create_manual_record(
    payload: HealthRecordManualCreate,
    user_id: str = Depends(get_current_user),
    record_repo: HealthRecordRepository = Depends(get_record_repo),
    param_repo: ClinicalParameterRepository = Depends(get_param_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """Create manual health record with parameters."""
    record = HealthRecord(
        user_id=user_id,
        record_type=payload.record_type,
        report_date=payload.report_date,
        is_processed=True,
        raw_text=payload.notes or "Manual entry",
    )
    record.validate()
    saved_record = await record_repo.create(record)

    # Save associated parameters
    param_models = []
    for p in payload.parameters:
        cp = ClinicalParameter(
            record_id=saved_record.record_id,
            param_name=p["param_name"],
            value=float(p["value"]),
            unit=p["unit"],
            reference_range_min=p.get("reference_range_min"),
            reference_range_max=p.get("reference_range_max"),
            report_date=payload.report_date,
        )
        cp.validate()
        param_models.append(cp)

    if param_models:
        await param_repo.create_many(param_models)

    # Invalidate cache and trigger trend update
    await cache.invalidate_user(user_id)
    asyncio.create_task(
        run_pipeline(
            record_id=saved_record.record_id,
            user_id=user_id,
            record_type=saved_record.record_type,
            raw_text=record.raw_text,
        )
    )

    return saved_record


@router.get("/", response_model=List[HealthRecordResponse])
async def list_records(
    skip: int = 0,
    limit: int = 50,
    user_id: str = Depends(get_current_user),
    record_repo: HealthRecordRepository = Depends(get_record_repo),
):
    """List all records for authenticated user."""
    return await record_repo.get_all(user_id=user_id, skip=skip, limit=limit)


@router.get("/{record_id}", response_model=HealthRecordResponse)
async def get_record(
    record_id: str,
    user_id: str = Depends(get_current_user),
    record_repo: HealthRecordRepository = Depends(get_record_repo),
):
    """Get single record by ID."""
    record = await record_repo.get_by_id(record_id, user_id)
    if not record:
        raise RecordNotFoundError(f"Record {record_id} not found")
    return record


@router.get("/{record_id}/download")
async def download_record_file(
    record_id: str,
    user_id: str = Depends(get_current_user),
    record_repo: HealthRecordRepository = Depends(get_record_repo),
    encryption_svc: EncryptionService = Depends(get_encryption_service),
):
    """
    Decrypts encrypted file in memory and streams it without caching.
    Per PRODUCTION_BACKEND.md §2.2.
    """
    record = await record_repo.get_by_id(record_id, user_id)
    if not record or not record.source_file_path or not os.path.exists(record.source_file_path):
        raise RecordNotFoundError("File not found or not yet available")

    with open(record.source_file_path, "rb") as f:
        encrypted_payload = f.read()

    decrypted_bytes = encryption_svc.decrypt_from_payload(encrypted_payload)

    # Determine response media type
    media_type = "application/pdf"
    if record.source_file_path.lower().endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"
    elif record.source_file_path.lower().endswith(".png"):
        media_type = "image/png"

    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, private",
        "Pragma": "no-cache",
        "Content-Disposition": f'attachment; filename="record_{record_id}.pdf"',
        "X-Content-Type-Options": "nosniff",
    }

    return StreamingResponse(
        io.BytesIO(decrypted_bytes),
        media_type=media_type,
        headers=headers,
    )


@router.put("/{record_id}", response_model=HealthRecordResponse)
async def update_record(
    record_id: str,
    payload: HealthRecordUpdate,
    user_id: str = Depends(get_current_user),
    record_repo: HealthRecordRepository = Depends(get_record_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """Update record metadata."""
    record = await record_repo.update_metadata(
        record_id=record_id,
        user_id=user_id,
        record_type=payload.record_type,
        report_date=payload.report_date,
    )
    if not record:
        raise RecordNotFoundError(f"Record {record_id} not found")

    await cache.invalidate("clinical_params", user_id)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: str,
    user_id: str = Depends(get_current_user),
    record_repo: HealthRecordRepository = Depends(get_record_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """Soft delete record."""
    success = await record_repo.soft_delete(record_id, user_id)
    if not success:
        raise RecordNotFoundError(f"Record {record_id} not found")

    await cache.invalidate_user(user_id)
    return None
