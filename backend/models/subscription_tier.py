"""
ArogyaMitra AI - SubscriptionTier Model (Phase 3)
Tracks user subscription plan and feature access gates.
Per FEATURES_PHASE3.md §2.5.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from backend.database import Base

VALID_TIERS = {"FREE", "PREMIUM", "PRO"}

TIER_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "FREE": {
        "family_member_limit": 2,
        "doctor_access_limit": 0,
        "prediction_enabled": False,
        "wearable_enabled": False,
        "api_access_enabled": False,
    },
    "PREMIUM": {
        "family_member_limit": 5,
        "doctor_access_limit": 3,
        "prediction_enabled": True,
        "wearable_enabled": True,
        "api_access_enabled": False,
    },
    "PRO": {
        "family_member_limit": 10,
        "doctor_access_limit": 999,
        "prediction_enabled": True,
        "wearable_enabled": True,
        "api_access_enabled": True,
    },
}

TIER_PRICES = {
    "PREMIUM": 29900,  # ₹299/month in paise
    "PRO": 79900,      # ₹799/month in paise
}


class SubscriptionTier(Base):
    __tablename__ = "subscription_tiers"

    subscription_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True, unique=True)
    tier = Column(String(20), nullable=False, default="FREE")
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)  # None = FREE (never expires)
    is_active = Column(Boolean, default=True, nullable=False)
    payment_reference = Column(String(100), nullable=True)
    family_member_limit = Column(Integer, nullable=False, default=2)
    doctor_access_limit = Column(Integer, nullable=False, default=0)
    prediction_enabled = Column(Boolean, default=False, nullable=False)
    wearable_enabled = Column(Boolean, default=False, nullable=False)
    api_access_enabled = Column(Boolean, default=False, nullable=False)

    def validate(self) -> None:
        if self.tier not in VALID_TIERS:
            raise ValueError(f"Tier must be one of: {', '.join(VALID_TIERS)}")
        if self.expires_at and self.expires_at <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")

    def is_expired(self) -> bool:
        """Returns True if subscription has a defined expiry and it has passed."""
        if not self.expires_at:
            return False  # FREE tier never expires
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else datetime.now(timezone.utc) > self.expires_at

    def days_remaining(self) -> Optional[int]:
        """Returns days until expiry, or None for FREE tier."""
        if not self.expires_at:
            return None
        expires = self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
        delta = expires - datetime.now(timezone.utc)
        return max(0, delta.days)

    def is_feature_available(self, feature: str) -> bool:
        """Check if a named feature is available on this subscription tier."""
        if self.is_expired() or not self.is_active:
            return False
        feature_map = {
            "prediction": self.prediction_enabled,
            "predictions": self.prediction_enabled,
            "wearable": self.wearable_enabled,
            "wearables": self.wearable_enabled,
            "api_access": self.api_access_enabled,
            "doctor_workspace": self.doctor_access_limit > 0,
            "voice": self.tier in ("PREMIUM", "PRO"),
            "whatsapp": self.tier == "PRO",
        }
        return feature_map.get(feature.lower(), False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "tier": self.tier,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "is_expired": self.is_expired(),
            "days_remaining": self.days_remaining(),
            "payment_reference": self.payment_reference,
            "limits": {
                "family_members": self.family_member_limit,
                "doctor_access": self.doctor_access_limit,
            },
            "features": {
                "prediction": self.prediction_enabled,
                "wearables": self.wearable_enabled,
                "api_access": self.api_access_enabled,
                "doctor_workspace": self.doctor_access_limit > 0,
                "voice": self.tier in ("PREMIUM", "PRO"),
                "whatsapp": self.tier == "PRO",
            },
        }

    @classmethod
    def create_free(cls, user_id: str) -> "SubscriptionTier":
        """Factory: create a FREE tier subscription for a new user."""
        defaults = TIER_DEFAULTS["FREE"]
        return cls(
            user_id=user_id,
            tier="FREE",
            **defaults,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubscriptionTier":
        started = data.get("started_at")
        if isinstance(started, str):
            started = datetime.fromisoformat(started)
        expires = data.get("expires_at")
        if isinstance(expires, str):
            expires = datetime.fromisoformat(expires)
        return cls(
            subscription_id=data.get("subscription_id", str(uuid.uuid4())),
            user_id=data["user_id"],
            tier=data.get("tier", "FREE"),
            started_at=started or datetime.now(timezone.utc),
            expires_at=expires,
            is_active=data.get("is_active", True),
            payment_reference=data.get("payment_reference"),
            family_member_limit=data.get("family_member_limit", 2),
            doctor_access_limit=data.get("doctor_access_limit", 0),
            prediction_enabled=data.get("prediction_enabled", False),
            wearable_enabled=data.get("wearable_enabled", False),
            api_access_enabled=data.get("api_access_enabled", False),
        )
