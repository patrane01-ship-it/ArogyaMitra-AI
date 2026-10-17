"""
ArogyaMitra AI - Phase 4 Consent & Privacy Management Service
Handles purpose-specific consent ledgers, grievance tracking, and audit logging.
Per PHASE4_IMPLEMENTATION.md F1, F2, F3.
"""

import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from backend.models.phase4_models import (
    ConsentRecord, GuardianConsent, DataExportJob, ErasureRequest,
    AuditLogEntry, PrivacyNoticeVersion
)
from backend.models.family_profile import FamilyProfile
from backend.exceptions.arogya_errors import (
    ConsentRequiredError, InvalidConsentPurposeError,
    GuardianConsentRequiredError, MinorFeatureRestrictedError,
    ErasureNotCancellableError
)
from backend.core.logger import logger

VALID_PURPOSES = {
    "CORE_SERVICE",
    "AI_PROCESSING",
    "WHATSAPP",
    "WEARABLE_SYNC",
    "ABDM_SYNC",
    "DOCTOR_SHARING",
    "RESEARCH_TRAINING",
    "MARKETING"
}


class PrivacyService:
    """Service handling consents, guardian attestations, exports, and erasure flows."""

    @staticmethod
    def get_privacy_notice(lang: str = "en") -> Dict[str, Any]:
        """Returns the versioned privacy notice text and metadata."""
        version = "2026.1"
        notice_text = (
            "ArogyaMitra AI Privacy Notice (DPDP Act 2023 & Rules 2025 Compliant). "
            "Your health data is processed solely for personal health tracking. "
            "Extracted records are processed via secured AI inference when you grant consent. "
            "You may withdraw consent, export all records, or request complete account erasure at any time."
        )
        text_hash = hashlib.sha256(notice_text.encode("utf-8")).hexdigest()
        return {
            "version": version,
            "language": lang,
            "notice_text": notice_text,
            "text_hash": text_hash,
            "effective_at": "2026-01-01T00:00:00Z"
        }

    @classmethod
    async def record_consent(
        cls,
        db: AsyncSession,
        user_id: str,
        purpose: str,
        granted: bool,
        notice_version: str,
        profile_id: Optional[str] = None,
        method: str = "WEB_UI"
    ) -> ConsentRecord:
        """Records an append-only consent entry in the consent ledger."""
        if purpose not in VALID_PURPOSES:
            raise InvalidConsentPurposeError(f"Unknown purpose: {purpose}")

        record = ConsentRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            profile_id=profile_id,
            purpose=purpose,
            granted=granted,
            notice_version=notice_version,
            method=method,
            recorded_at=datetime.now(timezone.utc)
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)

        # Log audit entry (PHI-free)
        await cls.log_audit(
            db=db,
            actor_type="USER",
            actor_id=user_id,
            action=f"CONSENT_{'GRANTED' if granted else 'WITHDRAWN'}_{purpose}",
            target_type="CONSENT",
            target_id=record.id,
            profile_id=profile_id
        )

        return record

    @classmethod
    async def has_consent(
        cls,
        db: AsyncSession,
        user_id: str,
        purpose: str,
        profile_id: Optional[str] = None
    ) -> bool:
        """Checks if active consent is currently granted for the given purpose."""
        query = select(ConsentRecord).where(
            and_(
                ConsentRecord.user_id == user_id,
                ConsentRecord.purpose == purpose
            )
        ).order_by(desc(ConsentRecord.recorded_at)).limit(1)

        result = await db.execute(query)
        latest = result.scalars().first()
        return latest.granted if latest else False

    @classmethod
    async def record_guardian_consent(
        cls,
        db: AsyncSession,
        profile_id: str,
        guardian_user_id: str,
        notice_version: str,
        method: str = "SELF_ATTESTATION"
    ) -> GuardianConsent:
        """Records verifiable parental/guardian consent for a minor profile."""
        guardian_consent = GuardianConsent(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            guardian_user_id=guardian_user_id,
            notice_version=notice_version,
            method=method,
            attested_at=datetime.now(timezone.utc)
        )
        db.add(guardian_consent)
        await db.commit()
        await db.refresh(guardian_consent)

        await cls.log_audit(
            db=db,
            actor_type="USER",
            actor_id=guardian_user_id,
            action="GUARDIAN_CONSENT_GRANTED",
            target_type="FAMILY_PROFILE",
            target_id=profile_id,
            profile_id=profile_id
        )

        return guardian_consent

    @classmethod
    async def request_erasure(
        cls,
        db: AsyncSession,
        user_id: str,
        scope: str = "PROFILE",
        profile_id: Optional[str] = None
    ) -> ErasureRequest:
        """Schedules a profile or account erasure with a 7-day cancellable grace period."""
        grace_until = datetime.now(timezone.utc) + timedelta(days=7)
        erasure = ErasureRequest(
            id=str(uuid.uuid4()),
            user_id=user_id,
            scope=scope,
            profile_id=profile_id,
            status="PENDING_GRACE",
            grace_until=grace_until,
            created_at=datetime.now(timezone.utc)
        )
        db.add(erasure)
        await db.commit()
        await db.refresh(erasure)

        await cls.log_audit(
            db=db,
            actor_type="USER",
            actor_id=user_id,
            action=f"ERASURE_REQUESTED_{scope}",
            target_type="ERASURE",
            target_id=erasure.id,
            profile_id=profile_id
        )
        return erasure

    @classmethod
    async def cancel_erasure(
        cls,
        db: AsyncSession,
        erasure_id: str,
        user_id: str
    ) -> ErasureRequest:
        """Cancels an active erasure request during its grace period."""
        query = select(ErasureRequest).where(
            and_(
                ErasureRequest.id == erasure_id,
                ErasureRequest.user_id == user_id
            )
        )
        result = await db.execute(query)
        erasure = result.scalars().first()
        if not erasure or erasure.status != "PENDING_GRACE":
            raise ErasureNotCancellableError()

        erasure.status = "CANCELLED"
        await db.commit()

        await cls.log_audit(
            db=db,
            actor_type="USER",
            actor_id=user_id,
            action="ERASURE_CANCELLED",
            target_type="ERASURE",
            target_id=erasure.id
        )
        return erasure

    @staticmethod
    async def log_audit(
        db: AsyncSession,
        actor_type: str,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: Optional[str] = None,
        profile_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_hash: Optional[str] = None
    ):
        """Creates an append-only, PHI-free audit log entry."""
        entry = AuditLogEntry(
            id=str(uuid.uuid4()),
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            profile_id=profile_id,
            request_id=request_id,
            ip_hash=ip_hash,
            occurred_at=datetime.now(timezone.utc)
        )
        db.add(entry)
        await db.commit()
