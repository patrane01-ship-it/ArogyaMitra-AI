"""
ArogyaMitra AI - ClinicalParameter Model
Represents an individual clinical test reading extracted from a health record.
Per FEATURES.md §2.2 and TECH_STACK.md §4.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from backend.database import Base
from backend.exceptions.arogya_errors import (
    InvalidParameterValueError,
    MissingUnitError,
)


class ParameterStatus(str, Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ClinicalParameter(Base):
    __tablename__ = "clinical_parameters"

    param_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id = Column(String(36), ForeignKey("health_records.record_id", ondelete="CASCADE"), nullable=False, index=True)
    param_name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    reference_range_min = Column(Float, nullable=True)
    reference_range_max = Column(Float, nullable=True)
    report_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="NORMAL")
    anomaly_score = Column(Float, nullable=True)
    # Phase 2 ML extensions
    isolation_forest_score = Column(Float, nullable=True)
    is_anomaly = Column(Boolean, nullable=True)
    ml_risk_contribution = Column(Float, nullable=True)

    def compute_status(self) -> str:
        """
        Compute status using threshold logic:
        - If value > ref_max * 2 -> CRITICAL
        - If value > ref_max -> HIGH
        - If ref_min is set and value < ref_min * 0.5 -> CRITICAL
        - If ref_min is set and value < ref_min -> LOW
        - Else NORMAL
        """
        val = float(self.value)
        ref_min = self.reference_range_min
        ref_max = self.reference_range_max

        if ref_max is not None:
            if val > (ref_max * 2):
                return ParameterStatus.CRITICAL.value
            elif val > ref_max:
                return ParameterStatus.HIGH.value

        if ref_min is not None:
            if val < (ref_min * 0.5):
                return ParameterStatus.CRITICAL.value
            elif val < ref_min:
                return ParameterStatus.LOW.value

        return ParameterStatus.NORMAL.value

    def validate(self):
        """Validate parameter properties."""
        try:
            val = float(self.value)
            if val < 0:
                raise InvalidParameterValueError("Clinical parameter value cannot be negative")
        except (ValueError, TypeError):
            raise InvalidParameterValueError(f"Invalid numeric value: {self.value}")

        if not self.unit or not str(self.unit).strip():
            raise MissingUnitError("Unit cannot be empty")

        # Auto-compute status
        self.status = self.compute_status()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity to dictionary."""
        return {
            "param_id": self.param_id,
            "record_id": self.record_id,
            "param_name": self.param_name,
            "value": self.value,
            "unit": self.unit,
            "reference_range_min": self.reference_range_min,
            "reference_range_max": self.reference_range_max,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "status": self.status,
            "anomaly_score": self.anomaly_score,
            "isolation_forest_score": self.isolation_forest_score,
            "is_anomaly": self.is_anomaly,
            "ml_risk_contribution": self.ml_risk_contribution,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClinicalParameter":
        """Deserialize from dictionary."""
        report_date = data.get("report_date")
        if isinstance(report_date, str):
            report_date = datetime.fromisoformat(report_date)

        inst = cls(
            param_id=data.get("param_id", str(uuid.uuid4())),
            record_id=data.get("record_id"),
            param_name=data.get("param_name"),
            value=float(data.get("value", 0.0)),
            unit=data.get("unit", ""),
            reference_range_min=data.get("reference_range_min"),
            reference_range_max=data.get("reference_range_max"),
            report_date=report_date or datetime.now(timezone.utc),
            status=data.get("status", "NORMAL"),
            anomaly_score=data.get("anomaly_score"),
            isolation_forest_score=data.get("isolation_forest_score"),
            is_anomaly=data.get("is_anomaly"),
            ml_risk_contribution=data.get("ml_risk_contribution"),
        )
        inst.validate()
        return inst
