"""
ArogyaMitra AI - Reminder Repository
Data access layer for Reminder with strict user_id scoping.
Per PRODUCTION_BACKEND.md §4.2, §6.3 and SECURITY_AUDIT.md §5.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.models.reminder import Reminder
from backend.core.logger import logger
from backend.exceptions.arogya_errors import ArogyaError, DatabaseError


class ReminderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, reminder: Reminder) -> Reminder:
        """Create a new reminder."""
        try:
            reminder.validate()
            self.db.add(reminder)
            await self.db.flush()
            return reminder
        except ArogyaError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:Reminder] Error creating reminder: {e}")
            raise DatabaseError("Failed to save reminder")

    async def create_many(self, reminders: List[Reminder]) -> List[Reminder]:
        """Bulk create reminders."""
        try:
            for r in reminders:
                r.validate()
                self.db.add(r)
            await self.db.flush()
            return reminders
        except ArogyaError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:Reminder] Error saving multiple reminders: {e}")
            raise DatabaseError("Failed to save reminders")

    async def get_by_id(self, reminder_id: str, user_id: str) -> Optional[Reminder]:
        """Fetch reminder by ID strictly scoped to user_id."""
        try:
            stmt = select(Reminder).where(
                Reminder.reminder_id == reminder_id,
                Reminder.user_id == user_id,
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:Reminder] Error getting reminder {reminder_id}: {e}")
            raise DatabaseError("Database error during reminder lookup")

    async def get_all(
        self, user_id: str, include_acknowledged: bool = False
    ) -> List[Reminder]:
        """Fetch reminders for a user, sorted by due_date ascending."""
        try:
            stmt = select(Reminder).where(
                Reminder.user_id == user_id,
                Reminder.is_active.is_(True),
            )
            if not include_acknowledged:
                stmt = stmt.where(Reminder.is_acknowledged.is_(False))

            stmt = stmt.order_by(Reminder.due_date.asc())
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"[Repo:Reminder] Error fetching reminders for user {user_id}: {e}")
            raise DatabaseError("Failed to fetch reminders")

    async def update(
        self,
        reminder_id: str,
        user_id: str,
        title: Optional[str] = None,
        due_date: Optional[datetime] = None,
        recurrence: Optional[str] = None,
        reminder_type: Optional[str] = None,
    ) -> Optional[Reminder]:
        """Update reminder properties."""
        reminder = await self.get_by_id(reminder_id, user_id)
        if not reminder:
            return None

        if title is not None:
            reminder.title = title
        if due_date is not None:
            reminder.due_date = due_date
        if recurrence is not None:
            reminder.recurrence = recurrence
        if reminder_type is not None:
            reminder.reminder_type = reminder_type

        try:
            reminder.validate()
            await self.db.flush()
            return reminder
        except ArogyaError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:Reminder] Error updating reminder {reminder_id}: {e}")
            raise DatabaseError("Failed to update reminder")

    async def acknowledge(self, reminder_id: str, user_id: str) -> Optional[Reminder]:
        """Mark reminder as acknowledged (idempotent)."""
        reminder = await self.get_by_id(reminder_id, user_id)
        if not reminder:
            return None
        reminder.is_acknowledged = True
        try:
            await self.db.flush()
            return reminder
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:Reminder] Error acknowledging reminder {reminder_id}: {e}")
            raise DatabaseError("Failed to acknowledge reminder")

    async def delete(self, reminder_id: str, user_id: str) -> bool:
        """Hard delete reminder per specification."""
        reminder = await self.get_by_id(reminder_id, user_id)
        if not reminder:
            return False
        try:
            await self.db.delete(reminder)
            await self.db.flush()
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:Reminder] Error deleting reminder {reminder_id}: {e}")
            raise DatabaseError("Failed to delete reminder")
