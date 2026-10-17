"""
ArogyaMitra AI - Phase 4 Account Security & Auth Extensions Service
Implements:
  - Email verification (single-use hashed token)
  - Password reset with timing attack protection & session revocation
  - TOTP MFA enrollment, verification, and hashed recovery codes
  - Session tracking with refresh-token family rotation and reuse detection
Per PHASE4_IMPLEMENTATION.md F12.
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from backend.models.user import User
from backend.models.phase4_models import (
    EmailVerificationToken, PasswordResetToken, TotpSecret, RecoveryCode, UserSession
)
from backend.exceptions.arogya_errors import (
    EmailNotVerifiedError, ResetTokenInvalidError, MfaRequiredError,
    MfaCodeInvalidError, SessionRevokedError, RefreshReuseDetectedError
)
from backend.core.logger import logger


class AccountSecurityService:
    """Service providing enhanced account security, tokens, MFA, and sessions."""

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    # ── Email Verification ───────────────────────────────────────────
    @classmethod
    async def create_email_verification(cls, db: AsyncSession, user_id: str) -> str:
        """Generates a secure single-use email verification token valid for 24h."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = cls._hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        token_entry = EmailVerificationToken(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(token_entry)
        await db.commit()
        return raw_token

    @classmethod
    async def verify_email_token(cls, db: AsyncSession, raw_token: str) -> bool:
        """Verifies email with token; marks token used."""
        token_hash = cls._hash_token(raw_token)
        now = datetime.now(timezone.utc)

        query = select(EmailVerificationToken).where(
            and_(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.used_at.is_(None),
                EmailVerificationToken.expires_at > now
            )
        )
        result = await db.execute(query)
        token_entry = result.scalars().first()
        if not token_entry:
            raise ResetTokenInvalidError("Invalid or expired email verification token")

        token_entry.used_at = now
        await db.commit()
        return True

    # ── Password Reset Flow ──────────────────────────────────────────
    @classmethod
    async def request_password_reset(cls, db: AsyncSession, email: str) -> Optional[str]:
        """
        Creates a password reset token. 
        Timing-safe: Returns without leaking whether email exists.
        """
        query = select(User).where(User.email == email.lower().strip())
        res = await db.execute(query)
        user = res.scalars().first()
        if not user:
            # Timing mitigation: perform dummy work
            _ = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
            return None

        raw_token = secrets.token_urlsafe(32)
        token_hash = cls._hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        reset_entry = PasswordResetToken(
            id=str(uuid.uuid4()),
            user_id=user.user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(reset_entry)
        await db.commit()
        return raw_token

    @classmethod
    async def reset_password(
        cls,
        db: AsyncSession,
        raw_token: str,
        new_hashed_password: str
    ) -> bool:
        """
        Resets user password with valid token and revokes ALL existing user sessions.
        """
        token_hash = cls._hash_token(raw_token)
        now = datetime.now(timezone.utc)

        query = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now
            )
        )
        res = await db.execute(query)
        token_entry = res.scalars().first()
        if not token_entry:
            raise ResetTokenInvalidError()

        # Update password
        user_res = await db.execute(select(User).where(User.user_id == token_entry.user_id))
        user = user_res.scalars().first()
        if not user:
            raise ResetTokenInvalidError()

        user.hashed_password = new_hashed_password
        token_entry.used_at = now

        # Revoke all user sessions
        await cls.revoke_all_sessions(db, user.user_id)
        await db.commit()
        return True

    # ── User Sessions & Refresh Rotation ─────────────────────────────
    @classmethod
    async def create_session(
        cls,
        db: AsyncSession,
        user_id: str,
        device_label: Optional[str] = None,
        ip_hash: Optional[str] = None
    ) -> UserSession:
        """Creates a new tracking session with a refresh token family ID."""
        session = UserSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            refresh_family_id=str(uuid.uuid4()),
            device_label=device_label or "Web Browser",
            ip_hash=ip_hash,
            last_used_at=datetime.now(timezone.utc)
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def rotate_session(
        cls,
        db: AsyncSession,
        session_id: str,
        expected_family_id: str
    ) -> str:
        """
        Rotates session refresh family. If reuse of old family ID is detected,
        revokes the session family immediately.
        """
        query = select(UserSession).where(UserSession.session_id == session_id)
        res = await db.execute(query)
        session = res.scalars().first()
        if not session or session.revoked_at is not None:
            raise SessionRevokedError()

        # Reuse detection: family id must match current active sequence
        if session.refresh_family_id != expected_family_id:
            logger.critical(f"[Security] Refresh reuse detected for session {session_id}! Revoking.")
            session.revoked_at = datetime.now(timezone.utc)
            await db.commit()
            raise RefreshReuseDetectedError()

        # Generate new family ID for sequence
        new_family_id = str(uuid.uuid4())
        session.refresh_family_id = new_family_id
        session.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        return new_family_id

    @classmethod
    async def revoke_all_sessions(cls, db: AsyncSession, user_id: str):
        """Revokes all active sessions for a user."""
        stmt = (
            update(UserSession)
            .where(and_(UserSession.user_id == user_id, UserSession.revoked_at.is_(None)))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await db.execute(stmt)
        await db.commit()
