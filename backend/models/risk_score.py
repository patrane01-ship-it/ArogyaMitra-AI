"""
ArogyaMitra AI - RiskScore Model
Stores computed overall and per-parameter health risk assessments.
Per FEATURES.md §2.3 and TECH_STACK.md §4.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List
from sqlalchemy import Column, String, Float, DateTime, Integer, JSON
from backend.database import Base
from backend.exceptions.arogya_errors import ArogyaError


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskScore(Base):
    __tablename__ = "risk_scores"

    score_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False, index=True)
    computed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    overall_risk = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    contributing_factors = Column(JSON, nullable=True)  # List of {param_name, value, weight, contribution}
    recommendations = Column(JSON, nullable=True)       # List of str recommendations
    version = Column(Integer, default=1, nullable=False)
    # Phase 2 ML extensions
    model_id = Column(String(36), nullable=True)
    model_version = Column(String(50), nullable=True)
    ml_confidence = Column(Float, nullable=True)
    scoring_method = Column(String(50), default="RULE_BASED", nullable=False)

    @staticmethod
    def compute_risk_level(score: float) -> str:
        """Map numeric risk score (0.0 - 1.0) to clinical category."""
        if score < 0.30:
            return RiskLevel.LOW.value
        elif score < 0.60:
            return RiskLevel.MODERATE.value
        elif score < 0.80:
            return RiskLevel.HIGH.value
        else:
            return RiskLevel.CRITICAL.value

    def validate(self):
        """Validate score boundaries."""
        if not (0.0 <= self.overall_risk <= 1.0):
            raise ArogyaError("overall_risk must be between 0.0 and 1.0", status_code=422)
        if not self.risk_level:
            self.risk_level = self.compute_risk_level(self.overall_risk)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity to dictionary."""
        return {
            "score_id": self.score_id,
            "user_id": self.user_id,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
            "overall_risk": round(self.overall_risk, 4),
            "risk_level": self.risk_level,
            "contributing_factors": self.contributing_factors or [],
            "recommendations": self.recommendations or [],
            "version": self.version,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "ml_confidence": self.ml_confidence,
            "scoring_method": self.scoring_method,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskScore":
        """Deserialize from dictionary."""
        computed_at = data.get("computed_at")
        if isinstance(computed_at, str):
            computed_at = datetime.fromisoformat(computed_at)

        overall = float(data.get("overall_risk", 0.0))
        inst = cls(
            score_id=data.get("score_id", str(uuid.uuid4())),
            user_id=data.get("user_id", "local_user"),
            computed_at=computed_at or datetime.now(timezone.utc),
            overall_risk=overall,
            risk_level=data.get("risk_level") or cls.compute_risk_level(overall),
            contributing_factors=data.get("contributing_factors", []),
            recommendations=data.get("recommendations", []),
            version=int(data.get("version", 1)),
            model_id=data.get("model_id"),
            model_version=data.get("model_version"),
            ml_confidence=data.get("ml_confidence"),
            scoring_method=data.get("scoring_method", "RULE_BASED"),
        )
        inst.validate()
        return inst
