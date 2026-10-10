"""
ArogyaMitra AI - DoctorReport Repository
Data access layer for DoctorReport with strict user_id scoping.
Per PRODUCTION_BACKEND.md §4.2, §6.3 and SECURITY_AUDIT.md §5.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.doctor_report import DoctorReport
from backend.core.logger import logger
from backend.exceptions.arogya_errors import ArogyaError, DatabaseError


class DoctorReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, report: DoctorReport) -> DoctorReport:
        """Create a new doctor report."""
        try:
            report.validate()
            self.db.add(report)
            await self.db.flush()
            return report
        except ArogyaError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:DoctorReport] Error creating report: {e}")
            raise DatabaseError("Failed to save doctor report")

    async def get_by_id(self, report_id: str, user_id: str) -> Optional[DoctorReport]:
        """Fetch report by ID scoped to user_id."""
        try:
            stmt = select(DoctorReport).where(
                DoctorReport.report_id == report_id,
                DoctorReport.user_id == user_id,
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:DoctorReport] Error getting report {report_id}: {e}")
            raise DatabaseError("Database error during report lookup")

    async def get_latest(self, user_id: str) -> Optional[DoctorReport]:
        """Fetch latest report for user."""
        try:
            stmt = (
                select(DoctorReport)
                .where(DoctorReport.user_id == user_id)
                .order_by(DoctorReport.generated_at.desc())
                .limit(1)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:DoctorReport] Error getting latest report: {e}")
            raise DatabaseError("Failed to fetch latest report")

    async def set_pdf_path(
        self, report_id: str, user_id: str, pdf_path: str
    ) -> Optional[DoctorReport]:
        """Attach generated PDF file path to report."""
        report = await self.get_by_id(report_id, user_id)
        if not report:
            return None
        report.pdf_path = pdf_path
        try:
            await self.db.flush()
            return report
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:DoctorReport] Error setting PDF path: {e}")
            raise DatabaseError("Failed to update PDF path")

    async def set_share_token(
        self, report_id: str, user_id: str, token: str, expires_at: datetime
    ) -> Optional[DoctorReport]:
        """Attach share token to report."""
        report = await self.get_by_id(report_id, user_id)
        if not report:
            return None
        report.share_token = token
        report.share_expires_at = expires_at
        try:
            await self.db.flush()
            return report
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:DoctorReport] Error setting share token: {e}")
            raise DatabaseError("Failed to save share token")

    async def get_by_share_token(self, token: str) -> Optional[DoctorReport]:
        """Public lookup by share token."""
        try:
            stmt = select(DoctorReport).where(DoctorReport.share_token == token)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:DoctorReport] Error lookup by share token: {e}")
            return None
