"""
ArogyaMitra AI - HealthRecord Repository
Data access layer for HealthRecord with strict user_id scoping for IDOR prevention.
Per PRODUCTION_BACKEND.md §4.2, §6.3 and SECURITY_AUDIT.md §5.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from backend.models.health_record import HealthRecord
from backend.core.logger import logger
from backend.exceptions.arogya_errors import (
    ArogyaError,
    DatabaseError,
    RecordAlreadyExistsError,
)


class HealthRecordRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, record: HealthRecord) -> HealthRecord:
        """Create a new health record."""
        try:
            self.db.add(record)
            await self.db.flush()
            return record
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"[Repo:HealthRecord] IntegrityError: {e}")
            raise RecordAlreadyExistsError("Record with this ID already exists")
        except OperationalError as e:
            await self.db.rollback()
            logger.critical(f"[Repo:HealthRecord] OperationalError: {e}")
            raise DatabaseError("Database unavailable during record creation")
        except Exception as e:
            await self.db.rollback()
            logger.exception(f"[Repo:HealthRecord] Unexpected error: {e}")
            raise ArogyaError("Failed to create health record", status_code=500)

    async def get_by_id(self, record_id: str, user_id: str) -> Optional[HealthRecord]:
        """Fetch a record by record_id strictly scoped to user_id (IDOR defense)."""
        try:
            stmt = select(HealthRecord).where(
                HealthRecord.record_id == record_id,
                HealthRecord.user_id == user_id,
                HealthRecord.is_deleted.is_(False),
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:HealthRecord] Error getting record {record_id}: {e}")
            raise DatabaseError("Database error during record lookup")

    async def get_all(
        self, user_id: str, skip: int = 0, limit: int = 50
    ) -> List[HealthRecord]:
        """Fetch all non-deleted records for a user with pagination."""
        try:
            limit = min(limit, 100)
            stmt = (
                select(HealthRecord)
                .where(
                    HealthRecord.user_id == user_id,
                    HealthRecord.is_deleted.is_(False),
                )
                .order_by(HealthRecord.upload_date.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"[Repo:HealthRecord] Error listing records for user {user_id}: {e}")
            raise DatabaseError("Database error during records list")

    async def update_metadata(
        self,
        record_id: str,
        user_id: str,
        record_type: Optional[str] = None,
        report_date: Optional[datetime] = None,
    ) -> Optional[HealthRecord]:
        """Update record type or report date."""
        record = await self.get_by_id(record_id, user_id)
        if not record:
            return None

        if record_type is not None:
            record.record_type = record_type
        if report_date is not None:
            record.report_date = report_date

        try:
            record.validate()
            await self.db.flush()
            return record
        except ArogyaError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:HealthRecord] Error updating record: {e}")
            raise DatabaseError("Failed to update record")

    async def mark_processed(
        self, record_id: str, user_id: str, raw_text: str, entities: dict
    ) -> Optional[HealthRecord]:
        """Mark record as processed with OCR raw text and extracted entities."""
        record = await self.get_by_id(record_id, user_id)
        if not record:
            return None
        record.raw_text = raw_text
        record.extracted_entities = entities
        record.is_processed = True
        try:
            await self.db.flush()
            return record
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:HealthRecord] Error marking processed: {e}")
            raise DatabaseError("Failed to update processing status")

    async def soft_delete(self, record_id: str, user_id: str) -> bool:
        """Soft delete record by setting is_deleted = True."""
        record = await self.get_by_id(record_id, user_id)
        if not record:
            return False
        record.is_deleted = True
        try:
            await self.db.flush()
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:HealthRecord] Error soft deleting record: {e}")
            raise DatabaseError("Failed to delete record")

    async def set_share_token(
        self, record_id: str, user_id: str, token: str, expires_at: datetime
    ) -> Optional[HealthRecord]:
        """Attach share token to record."""
        record = await self.get_by_id(record_id, user_id)
        if not record:
            return None
        record.share_token = token
        record.share_expires_at = expires_at
        await self.db.flush()
        return record

    async def get_by_share_token(self, token: str) -> Optional[HealthRecord]:
        """Fetch record by share token (used by public share view)."""
        try:
            stmt = select(HealthRecord).where(
                HealthRecord.share_token == token,
                HealthRecord.is_deleted.is_(False),
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:HealthRecord] Error fetching by share token: {e}")
            return None
