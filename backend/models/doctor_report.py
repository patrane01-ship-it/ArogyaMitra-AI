"""
ArogyaMitra AI - DoctorReport Model
Stores AI-generated pre-visit summaries for doctors and clinical consultations.
Per FEATURES.md §2.5 and TECH_STACK.md §4.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, DateTime, Text, JSON
from backend.database import Base
from backend.exceptions.arogya_errors import ArogyaError
from backend.services.share_service import ShareService


class DoctorReport(Base):
    __tablename__ = "doctor_reports"

    report_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False, default="local_user", index=True)
    generated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    report_content = Column(Text, nullable=False)
    pdf_path = Column(String(500), nullable=True)
    records_included = Column(JSON, nullable=True)  # List of record_ids
    share_token = Column(Text, nullable=True)
    share_expires_at = Column(DateTime, nullable=True)

    def validate(self):
        """Validate report content and record associations."""
        if not self.report_content or len(self.report_content.strip()) == 0:
            raise ArogyaError("Report content cannot be empty", status_code=422)
        if not self.records_included or len(self.records_included) == 0:
            raise ArogyaError("At least one record must be included in doctor report", status_code=400)

    def generate_share_token(self, expiry_hours: int = 24) -> str:
        """Create a signed, expiring share token."""
        result = ShareService.generate_token(
            resource_id=self.report_id,
            resource_type="report",
            user_id=self.user_id,
            expiry_hours=expiry_hours,
        )
        self.share_token = result["token"]
        self.share_expires_at = result["expires_at"]
        return self.share_token

    def is_share_valid(self) -> bool:
        """Check if current share token is still valid and unexpired."""
        if not self.share_token or not self.share_expires_at:
            return False
        expires = self.share_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < expires

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity to dictionary."""
        return {
            "report_id": self.report_id,
            "user_id": self.user_id,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "report_content": self.report_content,
            "pdf_path": self.pdf_path,
            "records_included": self.records_included or [],
            "share_token": self.share_token,
            "share_expires_at": self.share_expires_at.isoformat() if self.share_expires_at else None,
            "is_share_valid": self.is_share_valid(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DoctorReport":
        """Deserialize from dictionary."""
        generated_at = data.get("generated_at")
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at)

        share_expires_at = data.get("share_expires_at")
        if isinstance(share_expires_at, str):
            share_expires_at = datetime.fromisoformat(share_expires_at)

        inst = cls(
            report_id=data.get("report_id", str(uuid.uuid4())),
            user_id=data.get("user_id", "local_user"),
            generated_at=generated_at or datetime.now(timezone.utc),
            report_content=data.get("report_content", ""),
            pdf_path=data.get("pdf_path"),
            records_included=data.get("records_included", []),
            share_token=data.get("share_token"),
            share_expires_at=share_expires_at,
        )
        inst.validate()
        return inst
