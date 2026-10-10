"""
ArogyaMitra AI - Reminder Model
Tracks medication doses, clinical test appointments, and refill schedules.
Per FEATURES.md §2.4 and TECH_STACK.md §4.
"""

import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from backend.database import Base
from backend.exceptions.arogya_errors import (
    EmptyReminderTitleError,
    InvalidDueDateError,
    InvalidRecurrenceError,
)


class ReminderType(str, Enum):
    MEDICATION = "MEDICATION"
    TEST_DUE = "TEST_DUE"
    DOCTOR_VISIT = "DOCTOR_VISIT"
    REFILL = "REFILL"


class RecurrenceType(str, Enum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class Reminder(Base):
    __tablename__ = "reminders"

    reminder_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False, default="local_user", index=True)
    reminder_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    due_date = Column(DateTime, nullable=False, index=True)
    recurrence = Column(String(50), nullable=False, default="NONE")
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False, index=True)
    created_from_record_id = Column(String(36), ForeignKey("health_records.record_id", ondelete="SET NULL"), nullable=True)

    def validate(self):
        """Validate reminder attributes."""
        if not self.title or len(self.title.strip()) < 3:
            raise EmptyReminderTitleError("Reminder title must be at least 3 characters")

        valid_recurrences = {r.value for r in RecurrenceType}
        if self.recurrence not in valid_recurrences:
            raise InvalidRecurrenceError(f"Recurrence must be one of: {', '.join(valid_recurrences)}")

        now = datetime.now(timezone.utc)
        due = self.due_date
        if due:
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if due > now + timedelta(days=730):  # 2 years
                raise InvalidDueDateError("Due date cannot be more than 2 years in the future")

    def is_due_today(self) -> bool:
        """Check if reminder is due today."""
        if not self.due_date:
            return False
        now = datetime.now(timezone.utc)
        due = self.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        return due.date() == now.date()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity to dictionary."""
        return {
            "reminder_id": self.reminder_id,
            "user_id": self.user_id,
            "reminder_type": self.reminder_type,
            "title": self.title,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "recurrence": self.recurrence,
            "is_active": self.is_active,
            "is_acknowledged": self.is_acknowledged,
            "created_from_record_id": self.created_from_record_id,
            "is_due_today": self.is_due_today(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reminder":
        """Deserialize from dictionary."""
        due_date = data.get("due_date")
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)

        inst = cls(
            reminder_id=data.get("reminder_id", str(uuid.uuid4())),
            user_id=data.get("user_id", "local_user"),
            reminder_type=data.get("reminder_type", ReminderType.MEDICATION.value),
            title=data.get("title", ""),
            due_date=due_date or datetime.now(timezone.utc),
            recurrence=data.get("recurrence", RecurrenceType.NONE.value),
            is_active=data.get("is_active", True),
            is_acknowledged=data.get("is_acknowledged", False),
            created_from_record_id=data.get("created_from_record_id"),
        )
        inst.validate()
        return inst
