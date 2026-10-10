"""
ArogyaMitra AI - Reminder Schemas
Pydantic validation models for reminders and medication trackers.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    reminder_type: str = Field(..., description="MEDICATION, TEST_DUE, DOCTOR_VISIT, REFILL")
    title: str = Field(..., min_length=3)
    due_date: datetime
    recurrence: str = Field(default="NONE", description="NONE, DAILY, WEEKLY, MONTHLY")


class ReminderUpdate(BaseModel):
    reminder_type: Optional[str] = None
    title: Optional[str] = Field(None, min_length=3)
    due_date: Optional[datetime] = None
    recurrence: Optional[str] = None


class ReminderResponse(BaseModel):
    reminder_id: str
    user_id: str
    reminder_type: str
    title: str
    due_date: datetime
    recurrence: str
    is_active: bool
    is_acknowledged: bool
    created_from_record_id: Optional[str] = None
    is_due_today: bool = False

    class Config:
        from_attributes = True
