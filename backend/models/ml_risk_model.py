"""
ArogyaMitra AI - MLRiskModel Model
Metadata and serialized artifact registry for trained machine learning risk classifiers.
Per FEATURES_PHASE2.md §2.2 and TECH_STACK_PHASE2.md §3.
"""

import os
import uuid
import joblib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON, Text
from backend.database import Base
from backend.exceptions.arogya_errors import ArogyaError, ModelLoadError


class MLRiskModel(Base):
    __tablename__ = "ml_risk_models"

    model_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(100), nullable=False)
    trained_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    feature_names = Column(JSON, nullable=False)  # List[str] of 15 features
    training_accuracy = Column(Float, nullable=False)
    model_path = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    def validate(self):
        """Validate model record constraints."""
        if not (0.0 <= self.training_accuracy <= 1.0):
            raise ArogyaError("training_accuracy must be between 0.0 and 1.0", status_code=422)
        if not self.feature_names or len(self.feature_names) == 0:
            raise ArogyaError("feature_names list cannot be empty", status_code=422)

    def load(self):
        """Load and return serialized sklearn model object."""
        if not os.path.exists(self.model_path):
            raise ModelLoadError(f"Model file not found at: {self.model_path}")
        try:
            return joblib.load(self.model_path)
        except Exception as e:
            raise ModelLoadError(f"Failed to deserialize model {self.model_id}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize model metadata."""
        return {
            "model_id": self.model_id,
            "model_version": self.model_version,
            "model_type": self.model_type,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
            "feature_names": self.feature_names,
            "training_accuracy": round(self.training_accuracy, 4),
            "model_path": self.model_path,
            "is_active": self.is_active,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MLRiskModel":
        """Deserialize from dictionary."""
        trained_at = data.get("trained_at")
        if isinstance(trained_at, str):
            trained_at = datetime.fromisoformat(trained_at)

        return cls(
            model_id=data.get("model_id", str(uuid.uuid4())),
            model_version=data.get("model_version", "2.0.0"),
            model_type=data.get("model_type", "RandomForestClassifier"),
            trained_at=trained_at or datetime.now(timezone.utc),
            feature_names=data.get("feature_names", []),
            training_accuracy=float(data.get("training_accuracy", 0.0)),
            model_path=data.get("model_path", ""),
            is_active=data.get("is_active", False),
            notes=data.get("notes"),
        )
