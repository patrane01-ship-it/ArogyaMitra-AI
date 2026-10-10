"""
ArogyaMitra AI - PredictionResult Model (Phase 3)
Stores ML trajectory forecasts for clinical parameters.
Per FEATURES_PHASE3.md §2.3.
"""

import uuid
import math
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Float, Integer
from backend.database import Base


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    prediction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), nullable=False, index=True)
    param_name = Column(String(100), nullable=False)
    computed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    current_value = Column(Float, nullable=False)
    current_trend = Column(String(20), nullable=False)  # STABLE, IMPROVING, WORSENING, VOLATILE
    slope = Column(Float, nullable=False)
    months_to_threshold = Column(Integer, nullable=True)
    threshold_value = Column(Float, nullable=False)
    threshold_label = Column(String(200), nullable=False)
    confidence = Column(Float, nullable=False)
    data_points_used = Column(Integer, nullable=False)
    alert_level = Column(String(20), nullable=False)  # NONE, WATCH, WARN, URGENT
    narrative = Column(String(500), nullable=False)

    def validate(self) -> None:
        """Validate prediction result fields."""
        if not (0.0 <= self.confidence <= 1.0):
            self.confidence = max(0.0, min(1.0, self.confidence))  # clamp, never raise
        if not math.isfinite(self.slope):
            raise ValueError("Slope must be a finite number")
        if self.data_points_used < 1:
            raise ValueError("data_points_used must be at least 1")
        if self.months_to_threshold is not None and self.months_to_threshold <= 0:
            raise ValueError("months_to_threshold must be positive if set")

    def is_actionable(self) -> bool:
        """True if alert level warrants attention and confidence is sufficient."""
        return self.alert_level != "NONE" and self.confidence > 0.60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "profile_id": self.profile_id,
            "param_name": self.param_name,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
            "current_value": self.current_value,
            "current_trend": self.current_trend,
            "slope": round(self.slope, 6),
            "months_to_threshold": self.months_to_threshold,
            "threshold_value": self.threshold_value,
            "threshold_label": self.threshold_label,
            "confidence": round(self.confidence, 4),
            "data_points_used": self.data_points_used,
            "alert_level": self.alert_level,
            "narrative": self.narrative,
            "is_actionable": self.is_actionable(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PredictionResult":
        computed = data.get("computed_at")
        if isinstance(computed, str):
            computed = datetime.fromisoformat(computed)
        return cls(
            prediction_id=data.get("prediction_id", str(uuid.uuid4())),
            profile_id=data["profile_id"],
            param_name=data["param_name"],
            computed_at=computed or datetime.now(timezone.utc),
            current_value=float(data["current_value"]),
            current_trend=data.get("current_trend", "STABLE"),
            slope=float(data.get("slope", 0.0)),
            months_to_threshold=data.get("months_to_threshold"),
            threshold_value=float(data["threshold_value"]),
            threshold_label=data.get("threshold_label", ""),
            confidence=float(data.get("confidence", 0.0)),
            data_points_used=int(data.get("data_points_used", 0)),
            alert_level=data.get("alert_level", "NONE"),
            narrative=data.get("narrative", ""),
        )
