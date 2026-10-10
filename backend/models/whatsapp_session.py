"""
ArogyaMitra AI - WhatsAppSession Model (Phase 3)
Tracks WhatsApp bot sessions and OTP verification.
Per FEATURES_PHASE3.md §2.6.
"""

import re
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from sqlalchemy import Column, String, DateTime, Boolean
from backend.database import Base

_PHONE_REGEX = re.compile(r"^\+[1-9]\d{6,14}$")
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"

    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False, unique=True, index=True)
    verified_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    active_profile_id = Column(String(36), nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    conversation_state = Column(String, nullable=True)  # JSON
    otp_hash = Column(String(255), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)

    def validate(self) -> None:
        """Validate WhatsApp session data."""
        if not self.phone_number or not _PHONE_REGEX.match(self.phone_number):
            from backend.exceptions.arogya_errors import InvalidPhoneNumberError
            raise InvalidPhoneNumberError()

    def is_verified(self) -> bool:
        """Returns True if OTP has been confirmed."""
        return self.verified_at is not None

    def is_otp_valid(self, otp_plain: str) -> bool:
        """Verify OTP against hash and check expiry."""
        if not self.otp_hash or not self.otp_expires_at:
            return False
        expires = self.otp_expires_at.replace(tzinfo=timezone.utc) if self.otp_expires_at.tzinfo is None else self.otp_expires_at
        if datetime.now(timezone.utc) > expires:
            return False
        try:
            return _pwd_context.verify(otp_plain, self.otp_hash)
        except Exception:
            return False

    def set_otp(self, otp_plain: str) -> None:
        """Hash and store OTP."""
        self.otp_hash = _pwd_context.hash(otp_plain)

    def get_conversation_state(self) -> Dict[str, Any]:
        """Parse conversation_state JSON."""
        try:
            return json.loads(self.conversation_state or "{}")
        except Exception:
            return {}

    def set_conversation_state(self, state: Dict[str, Any]) -> None:
        self.conversation_state = json.dumps(state)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "phone_number": self.phone_number,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "is_active": self.is_active,
            "is_verified": self.is_verified(),
            "active_profile_id": self.active_profile_id,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WhatsAppSession":
        verified = data.get("verified_at")
        if isinstance(verified, str):
            verified = datetime.fromisoformat(verified)
        return cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            user_id=data["user_id"],
            phone_number=data["phone_number"],
            verified_at=verified,
            is_active=data.get("is_active", True),
            active_profile_id=data.get("active_profile_id"),
        )
