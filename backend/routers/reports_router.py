"""
ArogyaMitra AI - Reports Router
Endpoints for generating AI Doctor-Prep reports, streaming encrypted PDFs, and issuing share links.
Per PRODUCTION_BACKEND.md §10.6.
"""

import os
import io
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from backend.core.dependencies import (
    get_current_user,
    get_report_repo,
    get_encryption_service,
)
from backend.repositories.doctor_report_repo import DoctorReportRepository
from backend.services.encryption_service import EncryptionService
from backend.agents.doctor_prep_agent import DoctorPrepAgent
from backend.schemas.doctor_report_schema import (
    DoctorReportGenerateResponse,
    DoctorReportResponse,
    ShareTokenResponse,
)
from backend.exceptions.arogya_errors import RecordNotFoundError

router = APIRouter(prefix="/api/report", tags=["Doctor Reports"])


@router.post("/generate", status_code=status.HTTP_201_CREATED, response_model=DoctorReportGenerateResponse)
async def generate_doctor_report(
    user_id: str = Depends(get_current_user),
):
    """
    Generate an AI pre-visit Doctor-Prep report based on all historical and active records.
    Produces encrypted PDF on disk and returns structured summary.
    """
    result = await DoctorPrepAgent.generate_report(user_id=user_id)
    return result


@router.get("/latest", response_model=DoctorReportResponse)
async def get_latest_report(
    user_id: str = Depends(get_current_user),
    report_repo: DoctorReportRepository = Depends(get_report_repo),
):
    """Fetch latest AI Doctor-Prep report."""
    report = await report_repo.get_latest(user_id)
    if not report:
        raise RecordNotFoundError("No doctor report generated yet. Click generate to create one.")
    return report


@router.get("/{report_id}/pdf")
async def download_report_pdf(
    report_id: str,
    user_id: str = Depends(get_current_user),
    report_repo: DoctorReportRepository = Depends(get_report_repo),
    encryption_svc: EncryptionService = Depends(get_encryption_service),
):
    """
    Decrypts encrypted PDF in memory and streams to client without caching.
    Per PRODUCTION_BACKEND.md §2.2.
    """
    report = await report_repo.get_by_id(report_id, user_id)
    if not report or not report.pdf_path or not os.path.exists(report.pdf_path):
        raise RecordNotFoundError("PDF report not found or not yet generated")

    with open(report.pdf_path, "rb") as f:
        encrypted_bytes = f.read()

    decrypted_pdf = encryption_svc.decrypt_from_payload(encrypted_bytes)

    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, private",
        "Pragma": "no-cache",
        "Content-Disposition": f'attachment; filename="doctor_prep_report_{report_id}.pdf"',
        "X-Content-Type-Options": "nosniff",
    }

    return StreamingResponse(
        io.BytesIO(decrypted_pdf),
        media_type="application/pdf",
        headers=headers,
    )


@router.post("/{report_id}/share", response_model=ShareTokenResponse)
async def generate_share_link(
    report_id: str,
    expiry_hours: int = 24,
    user_id: str = Depends(get_current_user),
    report_repo: DoctorReportRepository = Depends(get_report_repo),
):
    """
    Generate an expiring share link for clinical consultation.
    """
    report = await report_repo.get_by_id(report_id, user_id)
    if not report:
        raise RecordNotFoundError(f"Report {report_id} not found")

    token = report.generate_share_token(expiry_hours=expiry_hours)
    await report_repo.set_share_token(
        report_id=report_id,
        user_id=user_id,
        token=token,
        expires_at=report.share_expires_at,
    )

    return {
        "share_url": f"/share/{token}",
        "expires_at": report.share_expires_at,
    }
