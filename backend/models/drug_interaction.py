"""
ArogyaMitra AI - DrugInteraction Model
Stores detected drug-drug interactions between medications across prescriptions.
Per FEATURES_PHASE2.md §2.4 and TECH_STACK_PHASE2.md §3.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey
from backend.database import Base
from backend.exceptions.arogya_errors import SameDrugInteractionError, InvalidSeverityError


class InteractionSeverity(str, Enum):
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    CONTRAINDICATED = "CONTRAINDICATED"


class DrugInteraction(Base):
    __tablename__ = "drug_interactions"

    interaction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    drug_a = Column(String(100), nullable=False)
    drug_b = Column(String(100), nullable=False)
    severity = Column(String(30), nullable=False, index=True)
    interaction_description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    source = Column(String(100), nullable=False, default="DrugBank")
    detected_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    from_record_ids = Column(JSON, nullable=True)  # List[str]
    is_dismissed = Column(Boolean, default=False, nullable=False, index=True)

    def validate(self):
        """Validate interaction consistency."""
        if self.drug_a.strip().lower() == self.drug_b.strip().lower():
            raise SameDrugInteractionError("Drug interaction cannot be evaluated on identical drugs")

        valid_severities = {s.value for s in InteractionSeverity}
        if self.severity not in valid_severities:
            raise InvalidSeverityError(f"Severity must be one of: {', '.join(valid_severities)}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize interaction object."""
        return {
            "interaction_id": self.interaction_id,
            "user_id": self.user_id,
            "drug_a": self.drug_a,
            "drug_b": self.drug_b,
            "severity": self.severity,
            "interaction_description": self.interaction_description,
            "recommendation": self.recommendation,
            "source": self.source,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "from_record_ids": self.from_record_ids or [],
            "is_dismissed": self.is_dismissed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DrugInteraction":
        """Deserialize from dictionary."""
        detected = data.get("detected_at")
        if isinstance(detected, str):
            detected = datetime.fromisoformat(detected)

        inst = cls(
            interaction_id=data.get("interaction_id", str(uuid.uuid4())),
            user_id=data.get("user_id"),
            drug_a=data.get("drug_a", "").strip(),
            drug_b=data.get("drug_b", "").strip(),
            severity=data.get("severity", InteractionSeverity.MODERATE.value),
            interaction_description=data.get("interaction_description", ""),
            recommendation=data.get("recommendation", ""),
            source=data.get("source", "DrugBank"),
            detected_at=detected or datetime.now(timezone.utc),
            from_record_ids=data.get("from_record_ids", []),
            is_dismissed=bool(data.get("is_dismissed", False)),
        )
        inst.validate()
        return inst
