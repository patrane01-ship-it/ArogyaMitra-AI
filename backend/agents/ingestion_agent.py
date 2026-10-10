"""
ArogyaMitra AI - Ingestion Agent
LangGraph node: Decrypts document, performs OCR, extracts clinical entities, and persists parameters.
Per TECH_STACK.md §3 and PRODUCTION_BACKEND.md §6.2, §9.2.
"""

import os
from typing import Dict, Any
from datetime import datetime, timezone
from backend.core.logger import logger
from backend.services.ocr_service import OCRService
from backend.services.entity_extractor import EntityExtractor
from backend.services.encryption_service import EncryptionService
from backend.config import settings
from backend.models.clinical_parameter import ClinicalParameter
from backend.database import get_async_session_factory
from backend.repositories.health_record_repo import HealthRecordRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.exceptions.arogya_errors import OCRExtractionError


async def ingestion_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Ingestion Agent node in LangGraph state machine."""
    record_id = state.get("record_id", "")
    user_id = state.get("user_id", "local_user")
    file_path = state.get("file_path")
    record_type = state.get("record_type", "LAB_REPORT")

    logger.info(f"[Agent:IngestionAgent] START | record_id={record_id}")
    state["current_step"] = "ingestion_running"

    try:
        raw_text = state.get("raw_text", "")

        # 1. If file_path provided and no raw_text yet, decrypt & perform OCR
        if file_path and os.path.exists(file_path) and not raw_text:
            encryption_svc = EncryptionService(settings.ENCRYPTION_KEY.encode())
            with open(file_path, "rb") as f:
                encrypted_payload = f.read()

            decrypted_bytes = encryption_svc.decrypt_from_payload(encrypted_payload)

            # Determine mime type from extension or file signature
            mime_type = "application/pdf"
            if file_path.lower().endswith((".png", ".jpg", ".jpeg")):
                mime_type = "image/jpeg" if file_path.lower().endswith((".jpg", ".jpeg")) else "image/png"

            ocr_svc = OCRService()
            raw_text = ocr_svc.extract_text(decrypted_bytes, mime_type)

        state["raw_text"] = raw_text

        # 2. Extract clinical parameters
        extractor = EntityExtractor()
        extracted_list = extractor.extract(raw_text) if raw_text else []
        state["extracted_entities"] = {"parameters": extracted_list}

        # 3. Save parameters and update record status in database
        async_factory = get_async_session_factory()
        async with async_factory() as session:
            record_repo = HealthRecordRepository(session)
            param_repo = ClinicalParameterRepository(session)

            # Mark HealthRecord as processed
            await record_repo.mark_processed(
                record_id=record_id,
                user_id=user_id,
                raw_text=raw_text,
                entities={"parameters": extracted_list},
            )

            # Create ClinicalParameter rows
            param_models = []
            for item in extracted_list:
                cp = ClinicalParameter(
                    record_id=record_id,
                    param_name=item["name"],
                    value=item["value"],
                    unit=item["unit"],
                    reference_range_min=item.get("ref_min"),
                    reference_range_max=item.get("ref_max"),
                    report_date=datetime.now(timezone.utc),
                )
                cp.validate()
                param_models.append(cp)

            if param_models:
                await param_repo.create_many(param_models)
                state["clinical_params"] = [p.to_dict() for p in param_models]
            else:
                state["clinical_params"] = []

            await session.commit()

        state["current_step"] = "ingestion_success"
        logger.info(f"[Agent:IngestionAgent] DONE | record_id={record_id} | params_extracted={len(extracted_list)}")

    except OCRExtractionError as e:
        logger.warning(f"[Agent:IngestionAgent] OCR_FAIL | record_id={record_id} | {e.message}")
        state["errors"].append({"agent": "ingestion", "error": e.error_code, "message": e.message})
        state["current_step"] = "ingestion_failed"
    except Exception as e:
        logger.exception(f"[Agent:IngestionAgent] FAIL | record_id={record_id} | {type(e).__name__}: {e}")
        state["errors"].append({"agent": "ingestion", "error": "UNEXPECTED", "message": str(e)})
        state["current_step"] = "ingestion_failed"

    return state
