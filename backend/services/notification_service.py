"""
ArogyaMitra AI - Phase 4 Smart Reminders, Adherence & Notifications Service
Implements timezone-aware reminders, adherence tracking, and quiet hours evaluation.
Per PHASE4_IMPLEMENTATION.md F9.
"""

import uuid
from datetime import datetime, timezone, time
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.models.reminder import Reminder
from backend.models.phase4_models import (
    NotificationPreference, ReminderDelivery, AdherenceLog
)
from backend.core.logger import logger


class NotificationAdherenceService:
    """Service managing smart notification delivery and patient medication adherence logs."""

    @classmethod
    async def get_or_create_preferences(
        cls, db: AsyncSession, user_id: str
    ) -> NotificationPreference:
        """Retrieves or creates default notification preferences."""
        res = await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        pref = res.scalars().first()
        if not pref:
            pref = NotificationPreference(
                id=str(uuid.uuid4()),
                user_id=user_id,
                channels=["IN_APP"],
                quiet_hours_start="22:00",
                quiet_hours_end="07:00",
                timezone="Asia/Kolkata",
                show_medication_names=False
            )
            db.add(pref)
            await db.commit()
            await db.refresh(pref)
        return pref

    @classmethod
    def is_in_quiet_hours(cls, pref: NotificationPreference, check_dt: datetime) -> bool:
        """Evaluates whether the given timestamp falls inside user quiet hours."""
        if not pref.quiet_hours_start or not pref.quiet_hours_end:
            return False

        try:
            start_parts = [int(p) for p in pref.quiet_hours_start.split(":")]
            end_parts = [int(p) for p in pref.quiet_hours_end.split(":")]
            t_start = time(start_parts[0], start_parts[1])
            t_end = time(end_parts[0], end_parts[1])
            current_t = check_dt.time()

            if t_start < t_end:
                return t_start <= current_t <= t_end
            else:
                # Spans midnight (e.g. 22:00 to 07:00)
                return current_t >= t_start or current_t <= t_end
        except Exception:
            return False

    @classmethod
    async def record_delivery(
        cls,
        db: AsyncSession,
        reminder_id: str,
        scheduled_for: datetime,
        channel: str,
        is_urgent: bool = False,
        pref: Optional[NotificationPreference] = None
    ) -> ReminderDelivery:
        """
        Idempotently enqueues/records reminder delivery.
        Respects quiet hours unless reminder is marked urgent.
        """
        # Idempotency check: (reminder_id, scheduled_for, channel)
        existing = await db.execute(
            select(ReminderDelivery).where(
                and_(
                    ReminderDelivery.reminder_id == reminder_id,
                    ReminderDelivery.scheduled_for == scheduled_for,
                    ReminderDelivery.channel == channel
                )
            )
        )
        record = existing.scalars().first()
        if record:
            return record

        status = "SCHEDULED"
        if pref and not is_urgent and cls.is_in_quiet_hours(pref, scheduled_for):
            status = "SKIPPED_QUIET_HOURS"
            logger.info(f"[Notification] Deferred reminder {reminder_id} due to quiet hours")

        delivery = ReminderDelivery(
            id=str(uuid.uuid4()),
            reminder_id=reminder_id,
            scheduled_for=scheduled_for,
            channel=channel,
            status=status,
            attempts=0
        )
        db.add(delivery)
        await db.commit()
        await db.refresh(delivery)
        return delivery

    @classmethod
    async def log_adherence(
        cls,
        db: AsyncSession,
        reminder_id: str,
        scheduled_for: datetime,
        status: str,  # TAKEN, SKIPPED, SNOOZED, MISSED
        snooze_minutes: Optional[int] = None
    ) -> AdherenceLog:
        """Logs patient medication adherence."""
        valid_statuses = {"TAKEN", "SKIPPED", "SNOOZED", "MISSED"}
        st = status.upper() if status.upper() in valid_statuses else "TAKEN"

        log = AdherenceLog(
            id=str(uuid.uuid4()),
            reminder_id=reminder_id,
            scheduled_for=scheduled_for,
            status=st,
            snooze_minutes=snooze_minutes,
            logged_at=datetime.now(timezone.utc)
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log
