"""
ArogyaMitra AI - APIKey Model (Phase 3)
B2B Health Score API key management (PRO tier only).
Per FEATURES_PHASE3.md §Feature 9.
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from backend.database import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    key_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    api_key_hash = Column(String(64), nullable=False)  # SHA-256 of plain key
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    rate_limit = Column(Integer, default=100, nullable=False)  # requests per hour

    def validate(self) -> None:
        if not self.name or len(self.name.strip()) < 3:
            raise ValueError("API key name must be at least 3 characters")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_active": self.is_active,
            "rate_limit": self.rate_limit,
        }

    @staticmethod
    def generate_key_pair() -> Tuple[str, str]:
        """
        Generate a new API key pair.
        Returns (plain_key, sha256_hash).
        The plain_key is shown ONCE to the user and never stored.
        Only the hash is stored in the database.
        """
        plain_key = secrets.token_hex(32)  # 64-char hex string
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        return plain_key, key_hash

    @staticmethod
    def hash_key(plain_key: str) -> str:
        """Hash a plain API key for lookup."""
        return hashlib.sha256(plain_key.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIKey":
        created = data.get("created_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        return cls(
            key_id=data.get("key_id", str(uuid.uuid4())),
            user_id=data["user_id"],
            api_key_hash=data["api_key_hash"],
            name=data["name"],
            created_at=created or datetime.now(timezone.utc),
            is_active=data.get("is_active", True),
            rate_limit=data.get("rate_limit", 100),
        )
