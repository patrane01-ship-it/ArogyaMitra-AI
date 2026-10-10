"""
ArogyaMitra AI - Public Share Router
Read-only public access endpoint for doctors using expiring JWT share tokens.
Per PRODUCTION_BACKEND.md §10.7.
"""

from fastapi import APIRouter, Depends, status
from backend.services.share_service import ShareService
from backend.database import get_async_session_factory
from backend.repositories.health_record_repo import HealthRecordRepository
from backend.repositories.doctor_report_repo import DoctorReportRepository
from backend.exceptions.arogya_errors import RecordNotFoundError

router = APIRouter(tags=["Public Share"])


@router.get("/share/{token}")
async def view_shared_resource(token: str):
    """
    Public read-only clinical consultation view.
    Validates token signature and expiration.
    Returns 410 Gone if expired, 401 if invalid.
    """
    payload = ShareService.verify_token(token)
    resource_id = payload.get("sub")
    resource_type = payload.get("resource_type")

    async_factory = get_async_session_factory()
    async with async_factory() as session:
        if resource_type == "report":
            report_repo = DoctorReportRepository(session)
            report = await report_repo.get_by_share_token(token)
            if not report:
                raise RecordNotFoundError("Shared doctor report not found or link has expired")
            return {
                "type": "doctor_report",
                "resource_id": report.report_id,
                "generated_at": report.generated_at,
                "content": report.report_content,
                "records_included": report.records_included,
            }
        else:
            record_repo = HealthRecordRepository(session)
            record = await record_repo.get_by_share_token(token)
            if not record:
                raise RecordNotFoundError("Shared health record not found or link has expired")
            return {
                "type": "health_record",
                "resource_id": record.record_id,
                "record_type": record.record_type,
                "report_date": record.report_date,
                "extracted_entities": record.extracted_entities,
            }
