"""
ArogyaMitra AI - Reminders Router
Endpoints for medication trackers, clinical appointments, and refill reminders.
Per PRODUCTION_BACKEND.md §10.5.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from backend.core.cache import ArogyaCache
from backend.core.dependencies import (
    get_current_user,
    get_reminder_repo,
    get_cache,
)
from backend.repositories.reminder_repo import ReminderRepository
from backend.models.reminder import Reminder
from backend.schemas.reminder_schema import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse,
)
from backend.exceptions.arogya_errors import RecordNotFoundError

router = APIRouter(prefix="/api/reminders", tags=["Reminders"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ReminderResponse)
async def create_reminder(
    payload: ReminderCreate,
    user_id: str = Depends(get_current_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """Create a new medication or appointment reminder."""
    reminder = Reminder(
        user_id=user_id,
        reminder_type=payload.reminder_type,
        title=payload.title,
        due_date=payload.due_date,
        recurrence=payload.recurrence,
        is_active=True,
        is_acknowledged=False,
    )
    reminder.validate()
    saved = await reminder_repo.create(reminder)

    await cache.invalidate("reminders_today", user_id)
    return saved


@router.get("/", response_model=List[ReminderResponse])
async def list_reminders(
    include_acknowledged: bool = False,
    user_id: str = Depends(get_current_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """
    List reminders for user.
    Cached for 60 seconds if requesting unacknowledged only.
    """
    if not include_acknowledged:
        cached = await cache.get("reminders_today", user_id)
        if cached is not None:
            return cached

    reminders = await reminder_repo.get_all(user_id=user_id, include_acknowledged=include_acknowledged)
    data = [r.to_dict() for r in reminders]

    if not include_acknowledged:
        await cache.set("reminders_today", user_id, data)

    return data


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: str,
    payload: ReminderUpdate,
    user_id: str = Depends(get_current_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """Update reminder schedule or details."""
    updated = await reminder_repo.update(
        reminder_id=reminder_id,
        user_id=user_id,
        title=payload.title,
        due_date=payload.due_date,
        recurrence=payload.recurrence,
        reminder_type=payload.reminder_type,
    )
    if not updated:
        raise RecordNotFoundError(f"Reminder {reminder_id} not found")

    await cache.invalidate("reminders_today", user_id)
    return updated


@router.patch("/{reminder_id}/ack", response_model=ReminderResponse)
async def acknowledge_reminder(
    reminder_id: str,
    user_id: str = Depends(get_current_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """Mark reminder as acknowledged."""
    acked = await reminder_repo.acknowledge(reminder_id, user_id)
    if not acked:
        raise RecordNotFoundError(f"Reminder {reminder_id} not found")

    await cache.invalidate("reminders_today", user_id)
    return acked


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: str,
    user_id: str = Depends(get_current_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """Delete a reminder."""
    success = await reminder_repo.delete(reminder_id, user_id)
    if not success:
        raise RecordNotFoundError(f"Reminder {reminder_id} not found")

    await cache.invalidate("reminders_today", user_id)
    return None
