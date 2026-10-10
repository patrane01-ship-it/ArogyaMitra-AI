"""
ArogyaMitra AI - AnomalyResult Model
Stores statistical anomaly detection results from Isolation Forest analysis on clinical parameters.
Per FEATURES_PHASE2.md §2.3 and TECH_STACK_PHASE2.md §3.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, Float, Boolean, Integer, ForeignKey
from backend.database import Base
from backend.exceptions.arogya_errors import ArogyaError


class AnomalyResult(Base):
    __tablename__ = "anomaly_results"

    anomaly_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    param_name = Column(String(100), nullable=False, index=True)
    computed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    anomaly_score = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, nullable=False, index=True)
    threshold = Column(Float, default=-0.1, nullable=False)
    data_points_used = Column(Integer, nullable=False)
    flagged_reading_date = Column(DateTime, nullable=True)
    flagged_value = Column(Float, nullable=True)

    def validate(self):
        """Validate anomaly boundaries."""
        if not (-1.0 <= self.anomaly_score <= 1.0):
            raise ArogyaError("anomaly_score must be within expected bounds", status_code=422)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize anomaly entity."""
        return {
            "anomaly_id": self.anomaly_id,
            "user_id": self.user_id,
            "param_name": self.param_name,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
            "anomaly_score": round(self.anomaly_score, 4),
            "is_anomaly": self.is_anomaly,
            "threshold": self.threshold,
            "data_points_used": self.data_points_used,
            "flagged_reading_date": self.flagged_reading_date.isoformat() if self.flagged_reading_date else None,
            "flagged_value": self.flagged_value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnomalyResult":
        """Deserialize from dictionary."""
        computed_at = data.get("computed_at")
        if isinstance(computed_at, str):
            computed_at = datetime.fromisoformat(computed_at)
        flagged_date = data.get("flagged_reading_date")
        if isinstance(flagged_date, str):
            flagged_date = datetime.fromisoformat(flagged_date)

        return cls(
            anomaly_id=data.get("anomaly_id", str(uuid.uuid4())),
            user_id=data.get("user_id"),
            param_name=data.get("param_name"),
            computed_at=computed_at or datetime.now(timezone.utc),
            anomaly_score=float(data.get("anomaly_score", 0.0)),
            is_anomaly=bool(data.get("is_anomaly", False)),
            threshold=float(data.get("threshold", -0.1)),
            data_points_used=int(data.get("data_points_used", 0)),
            flagged_reading_date=flagged_date,
            flagged_value=data.get("flagged_value"),
        )
