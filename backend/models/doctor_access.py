"""
ArogyaMitra AI - DoctorAccess Model (Phase 3)
Grants read-only doctor workspace access to a patient profile.
Per FEATURES_PHASE3.md §2.4.
"""

import re
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from backend.database import Base

VALID_SCOPE_VALUES = {"records", "timeline", "risk", "medications", "predictions"}
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")


class DoctorAccess(Base):
    __tablename__ = "doctor_access"

    access_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_profile_id = Column(String(36), nullable=False, index=True)
    granted_by_user_id = Column(String(36), nullable=False)
    doctor_name = Column(String(100), nullable=False)
    doctor_email = Column(String(255), nullable=False)
    doctor_registration_number = Column(String(50), nullable=True)
    specialization = Column(String(100), nullable=True)
    access_token = Column(String(36), nullable=False, unique=True, index=True,
                         default=lambda: str(uuid.uuid4()))
    granted_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    scope_json = Column(String(500), nullable=False, default='["records","timeline","risk"]')

    def validate(self) -> None:
        if not self.doctor_name or len(self.doctor_name.strip()) < 2:
            raise ValueError("Doctor name must be at least 2 characters")
        if not self.doctor_email or not EMAIL_REGEX.match(self.doctor_email):
            raise ValueError("Invalid doctor email address")
        if not self.expires_at or self.expires_at <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")
        scope = self.get_scope()
        if not scope:
            raise ValueError("Scope cannot be empty")
        invalid = set(scope) - VALID_SCOPE_VALUES
        if invalid:
            raise ValueError(f"Invalid scope values: {invalid}. Valid: {VALID_SCOPE_VALUES}")

    def is_expired(self) -> bool:
        """Returns True if access has expired or been deactivated."""
        if not self.is_active:
            return True
        expires = self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
        return datetime.now(timezone.utc) > expires

    def get_scope(self) -> List[str]:
        """Parse scope_json to list."""
        try:
            return json.loads(self.scope_json or "[]")
        except Exception:
            return []

    def set_scope(self, scope_list: List[str]) -> None:
        """Store scope list as JSON string."""
        self.scope_json = json.dumps(scope_list)

    def generate_workspace_url(self, base_url: str = "") -> str:
        return f"{base_url}/doctor-view/{self.access_token}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "access_id": self.access_id,
            "patient_profile_id": self.patient_profile_id,
            "granted_by_user_id": self.granted_by_user_id,
            "doctor_name": self.doctor_name,
            "doctor_email": self.doctor_email,
            "doctor_registration_number": self.doctor_registration_number,
            "specialization": self.specialization,
            "access_token": self.access_token,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "access_count": self.access_count,
            "is_active": self.is_active,
            "is_expired": self.is_expired(),
            "scope": self.get_scope(),
            "workspace_url": self.generate_workspace_url(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DoctorAccess":
        granted = data.get("granted_at")
        if isinstance(granted, str):
            granted = datetime.fromisoformat(granted)
        expires = data.get("expires_at")
        if isinstance(expires, str):
            expires = datetime.fromisoformat(expires)
        obj = cls(
            access_id=data.get("access_id", str(uuid.uuid4())),
            patient_profile_id=data["patient_profile_id"],
            granted_by_user_id=data["granted_by_user_id"],
            doctor_name=data["doctor_name"],
            doctor_email=data["doctor_email"],
            doctor_registration_number=data.get("doctor_registration_number"),
            specialization=data.get("specialization"),
            access_token=data.get("access_token", str(uuid.uuid4())),
            granted_at=granted or datetime.now(timezone.utc),
            expires_at=expires or (datetime.now(timezone.utc) + timedelta(days=30)),
            is_active=data.get("is_active", True),
            access_count=data.get("access_count", 0),
        )
        obj.set_scope(data.get("scope", ["records", "timeline", "risk"]))
        return obj
