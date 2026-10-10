"""
ArogyaMitra AI - WearableReading Model (Phase 3)
Stores passive vitals readings from connected wearable devices.
Per FEATURES_PHASE3.md §2.2.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Float, Boolean
from backend.database import Base

VALID_SOURCES = {"FITBIT", "MI_BAND", "GARMIN", "SAMSUNG_HEALTH", "MANUAL"}
VALID_METRIC_TYPES = {"HEART_RATE", "STEPS", "SLEEP_HOURS", "BLOOD_OXYGEN", "WEIGHT", "STRESS_SCORE"}
CLINICAL_CONVERTIBLE = {"HEART_RATE", "BLOOD_OXYGEN"}


class WearableReading(Base):
    __tablename__ = "wearable_readings"

    reading_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), nullable=False, index=True)
    source = Column(String(30), nullable=False)
    metric_type = Column(String(30), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    synced_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    raw_payload = Column(String, nullable=True)  # JSON string
    is_anomaly = Column(Boolean, default=False, nullable=False)

    def validate(self) -> None:
        """Validate wearable reading data."""
        if self.value <= 0:
            raise ValueError("Wearable reading value must be positive")
        if self.source not in VALID_SOURCES:
            raise ValueError(f"Source must be one of: {', '.join(VALID_SOURCES)}")
        if self.metric_type not in VALID_METRIC_TYPES:
            raise ValueError(f"Metric type must be one of: {', '.join(VALID_METRIC_TYPES)}")
        if self.recorded_at and self.recorded_at > datetime.now(timezone.utc):
            raise ValueError("recorded_at cannot be in the future")

    def is_clinical_convertible(self) -> bool:
        """Returns True if this reading can be converted to a ClinicalParameter."""
        return self.metric_type in CLINICAL_CONVERTIBLE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reading_id": self.reading_id,
            "profile_id": self.profile_id,
            "source": self.source,
            "metric_type": self.metric_type,
            "value": self.value,
            "unit": self.unit,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
            "is_anomaly": self.is_anomaly,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WearableReading":
        recorded = data.get("recorded_at")
        if isinstance(recorded, str):
            recorded = datetime.fromisoformat(recorded)
        synced = data.get("synced_at")
        if isinstance(synced, str):
            synced = datetime.fromisoformat(synced)
        return cls(
            reading_id=data.get("reading_id", str(uuid.uuid4())),
            profile_id=data["profile_id"],
            source=data["source"],
            metric_type=data["metric_type"],
            value=float(data["value"]),
            unit=data.get("unit", ""),
            recorded_at=recorded,
            synced_at=synced or datetime.now(timezone.utc),
            raw_payload=data.get("raw_payload"),
            is_anomaly=data.get("is_anomaly", False),
        )
