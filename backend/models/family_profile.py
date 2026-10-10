"""
ArogyaMitra AI - FamilyProfile Model (Phase 3)
Groups multiple health members under one account owner.
Per FEATURES_PHASE3.md §2.1.
"""

import re
import uuid
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Date, Boolean
from backend.database import Base
from backend.exceptions.arogya_errors import (
    InvalidABHAIDError,
    FutureDateOfBirthError,
    InvalidNameError,
)

VALID_RELATIONS = {"SELF", "SPOUSE", "PARENT", "CHILD", "SIBLING", "OTHER"}
VALID_GENDERS = {"MALE", "FEMALE", "OTHER"}
_ABHA_REGEX = re.compile(r"^\d{14}$")


class FamilyProfile(Base):
    __tablename__ = "family_profiles"

    profile_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id = Column(String(36), nullable=False, index=True)
    member_name = Column(String(100), nullable=False)
    relation = Column(String(20), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    abha_id = Column(String(20), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True, nullable=False)

    def validate(self) -> None:
        """Validate family profile data."""
        if not self.member_name or len(self.member_name.strip()) < 2:
            raise InvalidNameError("Member name must be at least 2 characters")
        if self.relation not in VALID_RELATIONS:
            raise ValueError(f"Relation must be one of: {', '.join(VALID_RELATIONS)}")
        if self.abha_id and not _ABHA_REGEX.match(self.abha_id):
            raise InvalidABHAIDError()
        if self.date_of_birth and self.date_of_birth > date.today():
            raise FutureDateOfBirthError()

    def compute_age(self) -> Optional[int]:
        """Compute age in years from date_of_birth."""
        if not self.date_of_birth:
            return None
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "owner_user_id": self.owner_user_id,
            "member_name": self.member_name,
            "relation": self.relation,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "abha_id": self.abha_id,
            "is_primary": self.is_primary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "age": self.compute_age(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FamilyProfile":
        dob = data.get("date_of_birth")
        if isinstance(dob, str):
            dob = date.fromisoformat(dob)
        created = data.get("created_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        return cls(
            profile_id=data.get("profile_id", str(uuid.uuid4())),
            owner_user_id=data.get("owner_user_id", ""),
            member_name=data.get("member_name", ""),
            relation=data.get("relation", "SELF"),
            date_of_birth=dob,
            gender=data.get("gender"),
            abha_id=data.get("abha_id"),
            is_primary=data.get("is_primary", False),
            created_at=created or datetime.now(timezone.utc),
            is_active=data.get("is_active", True),
        )
