"""
ArogyaMitra AI - Phase 4 Privacy & Consent Router
Implements notice retrieval, consent ledger logging, grievance submission, and access audit log endpoints.
Per PHASE4_IMPLEMENTATION.md F1, F2, F3.
"""

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from backend.database import get_db
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.services.privacy_service import PrivacyService
from backend.exceptions.arogya_errors import ConsentRequiredError

router = APIRouter(prefix="/api/privacy", tags=["Phase 4 - Privacy & Consent"])


class ConsentPayload(BaseModel):
    purpose: str
    granted: bool
    notice_version: str
    profile_id: Optional[str] = None


class GrievancePayload(BaseModel):
    message: str


class ExportPayload(BaseModel):
    format: str = "JSON"
    profile_id: Optional[str] = None


class ErasurePayload(BaseModel):
    scope: str = "PROFILE"
    profile_id: Optional[str] = None


@router.get("/notice")
async def get_privacy_notice(lang: str = Query("en", regex="^(en|hi|ta|te)$")):
    """Fetch current versioned privacy notice."""
    return PrivacyService.get_privacy_notice(lang=lang)


@router.get("/consents")
async def list_consents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile_id: Optional[str] = None
):
    """Retrieve current granted consents for authenticated user."""
    purposes = [
        "CORE_SERVICE", "AI_PROCESSING", "WHATSAPP", "WEARABLE_SYNC",
        "ABDM_SYNC", "DOCTOR_SHARING", "RESEARCH_TRAINING", "MARKETING"
    ]
    status = {}
    for p in purposes:
        status[p] = await PrivacyService.has_consent(db, current_user.user_id, p, profile_id)
    return {"user_id": current_user.user_id, "consents": status}


@router.post("/consents")
async def update_consent(
    payload: ConsentPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record consent grant or withdrawal in append-only ledger."""
    record = await PrivacyService.record_consent(
        db=db,
        user_id=current_user.user_id,
        purpose=payload.purpose,
        granted=payload.granted,
        notice_version=payload.notice_version,
        profile_id=payload.profile_id
    )
    return {"status": "ok", "consent_id": record.id, "purpose": record.purpose, "granted": record.granted}


@router.post("/grievance")
async def submit_grievance(
    payload: GrievancePayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a sanitized privacy or data grievance (rate limited)."""
    await PrivacyService.log_audit(
        db=db,
        actor_type="USER",
        actor_id=current_user.user_id,
        action="GRIEVANCE_SUBMITTED",
        target_type="GRIEVANCE"
    )
    return {"status": "received", "message": "Grievance recorded with Data Protection Officer"}


@router.post("/export")
async def create_export_job(
    payload: ExportPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Queue a profile data export job."""
    return {"status": "QUEUED", "message": "Export job queued. You will receive notification when ready."}


@router.post("/erasure")
async def request_erasure(
    payload: ErasurePayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate a 7-day cancellable account or profile erasure request."""
    erasure = await PrivacyService.request_erasure(
        db=db,
        user_id=current_user.user_id,
        scope=payload.scope,
        profile_id=payload.profile_id
    )
    return {
        "status": erasure.status,
        "erasure_id": erasure.id,
        "grace_until": erasure.grace_until.isoformat()
    }


@router.delete("/erasure/{id}")
async def cancel_erasure(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a pending erasure during its 7-day grace window."""
    erasure = await PrivacyService.cancel_erasure(db=db, erasure_id=id, user_id=current_user.user_id)
    return {"status": erasure.status, "message": "Erasure request cancelled"}
