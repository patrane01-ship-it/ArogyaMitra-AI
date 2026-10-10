"""
ArogyaMitra AI - User Model
Multi-user authentication, credentials, and profile management.
Per FEATURES_PHASE2.md §2.1 and TECH_STACK_PHASE2.md §3.
"""

import re
import uuid
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Date, Boolean
from passlib.context import CryptContext
from backend.database import Base
from backend.exceptions.arogya_errors import (
    InvalidEmailError,
    InvalidNameError,
    FutureDateOfBirthError,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    refresh_token_hash = Column(String(255), nullable=True)

    def validate(self):
        """Validate user registration data."""
        if not self.email or not EMAIL_REGEX.match(self.email):
            raise InvalidEmailError("Invalid email address format")
        if not self.full_name or len(self.full_name.strip()) < 2:
            raise InvalidNameError("Full name must be at least 2 characters")
        if self.date_of_birth:
            today = date.today()
            if self.date_of_birth > today:
                raise FutureDateOfBirthError("Date of birth cannot be in the future")

    def set_password(self, plain_password: str):
        """Hash and store password."""
        self.hashed_password = pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        """Verify plain password against bcrypt hash."""
        return pwd_context.verify(plain_password, self.hashed_password)

    def compute_age(self) -> Optional[int]:
        """Compute age in years."""
        if not self.date_of_birth:
            return None
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize user data (excluding password and token secrets)."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "age": self.compute_age(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Deserialize from dictionary."""
        dob = data.get("date_of_birth")
        if isinstance(dob, str):
            dob = date.fromisoformat(dob)
        created = data.get("created_at")
        if isinstance(created, str):
            created = datetime.fromisoformat(created)

        user = cls(
            user_id=data.get("user_id", str(uuid.uuid4())),
            email=data.get("email"),
            hashed_password=data.get("hashed_password", ""),
            full_name=data.get("full_name"),
            date_of_birth=dob,
            gender=data.get("gender"),
            created_at=created or datetime.now(timezone.utc),
            is_active=data.get("is_active", True),
            refresh_token_hash=data.get("refresh_token_hash"),
        )
        return user
