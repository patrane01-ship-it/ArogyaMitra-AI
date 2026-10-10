"""
ArogyaMitra AI - HealthRecord Model
Represents an uploaded medical document (lab report, prescription, etc.)
Per FEATURES.md §2.1 and TECH_STACK.md §4.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text
from backend.database import Base
from backend.exceptions.arogya_errors import (
    InvalidRecordTypeError,
    FutureDateError,
    OCRExtractionError,
)
from backend.services.share_service import ShareService


class RecordType(str, Enum):
    LAB_REPORT = "LAB_REPORT"
    PRESCRIPTION = "PRESCRIPTION"
    DOCTOR_NOTE = "DOCTOR_NOTE"
    IMAGING = "IMAGING"
    MANUAL_ENTRY = "MANUAL_ENTRY"


class HealthRecord(Base):
    __tablename__ = "health_records"

    record_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False, default="local_user", index=True)
    record_type = Column(String(50), nullable=False)
    upload_date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    report_date = Column(DateTime, nullable=False)
    source_file_path = Column(String(500), nullable=True)
    raw_text = Column(Text, nullable=True)
    extracted_entities = Column(JSON, nullable=True)
    encryption_hash = Column(String(128), nullable=True)
    is_processed = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    share_token = Column(Text, nullable=True)
    share_expires_at = Column(DateTime, nullable=True)

    def validate(self):
        """Validate model integrity against business rules."""
        valid_types = {e.value for e in RecordType}
        if self.record_type not in valid_types:
            raise InvalidRecordTypeError(
                f"record_type must be one of: {', '.join(valid_types)}"
            )

        now = datetime.now(timezone.utc)
        # Handle naive or aware datetimes
        report_dt = self.report_date
        if report_dt:
            if report_dt.tzinfo is None:
                report_dt = report_dt.replace(tzinfo=timezone.utc)
            if report_dt > now:
                raise FutureDateError("Report date cannot be in the future")

        if self.is_processed and not self.raw_text:
            raise OCRExtractionError("Processed record must contain raw text")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity to dictionary."""
        return {
            "record_id": self.record_id,
            "user_id": self.user_id,
            "record_type": self.record_type,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "source_file_path": self.source_file_path,
            "raw_text": self.raw_text,
            "extracted_entities": self.extracted_entities,
            "encryption_hash": self.encryption_hash,
            "is_processed": self.is_processed,
            "is_deleted": self.is_deleted,
            "share_token": self.share_token,
            "share_expires_at": self.share_expires_at.isoformat() if self.share_expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealthRecord":
        """Deserialize from dictionary."""
        report_date = data.get("report_date")
        if isinstance(report_date, str):
            report_date = datetime.fromisoformat(report_date)

        upload_date = data.get("upload_date")
        if isinstance(upload_date, str):
            upload_date = datetime.fromisoformat(upload_date)

        share_expires_at = data.get("share_expires_at")
        if isinstance(share_expires_at, str):
            share_expires_at = datetime.fromisoformat(share_expires_at)

        return cls(
            record_id=data.get("record_id", str(uuid.uuid4())),
            user_id=data.get("user_id", "local_user"),
            record_type=data.get("record_type"),
            upload_date=upload_date or datetime.now(timezone.utc),
            report_date=report_date or datetime.now(timezone.utc),
            source_file_path=data.get("source_file_path"),
            raw_text=data.get("raw_text"),
            extracted_entities=data.get("extracted_entities"),
            encryption_hash=data.get("encryption_hash"),
            is_processed=data.get("is_processed", False),
            is_deleted=data.get("is_deleted", False),
            share_token=data.get("share_token"),
            share_expires_at=share_expires_at,
        )

    def generate_share_token(self, expiry_hours: int = 24) -> str:
        """Create a signed, expiring share token."""
        result = ShareService.generate_token(
            resource_id=self.record_id,
            resource_type="record",
            user_id=self.user_id,
            expiry_hours=expiry_hours,
        )
        self.share_token = result["token"]
        self.share_expires_at = result["expires_at"]
        return self.share_token

    def is_share_valid(self) -> bool:
        """Check if current share token is still valid and not expired."""
        if not self.share_token or not self.share_expires_at:
            return False
        expires = self.share_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < expires
