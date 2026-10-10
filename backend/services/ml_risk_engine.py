"""
ArogyaMitra AI - ML Risk Engine (Phase 2)
scikit-learn based health risk prediction with rule-based fallback.
Per FEATURES_PHASE2.md §2.2 and TECH_STACK_PHASE2.md §4.
"""

import os
import joblib
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from backend.config import settings, SUPPORTED_PARAMETERS
from backend.core.logger import logger
from backend.exceptions.arogya_errors import (
    InvalidFeatureVectorError,
    ModelLoadError,
    ModelNotFoundError,
)

# Ordered parameter list for consistent feature vector construction
FEATURE_ORDER = list(SUPPORTED_PARAMETERS.keys())  # 15 parameters

# Risk level thresholds (consistent with rule engine)
RISK_THRESHOLDS = {
    "CRITICAL": 0.75,
    "HIGH": 0.50,
    "MODERATE": 0.25,
}


class MLRiskEngine:
    """
    ML-powered health risk prediction engine.
    Loads a scikit-learn pipeline (e.g., RandomForest + StandardScaler).
    Falls back to rule-based scoring if no model is loaded.
    """

    _model = None  # Shared class-level model instance
    _model_loaded: bool = False
    _model_version: Optional[str] = None

    @classmethod
    def load_model(cls, model_path: Optional[str] = None) -> bool:
        """
        Load ML model from disk. Silently falls back to rule-based if file missing.
        Returns True if ML model loaded, False if falling back.
        """
        path = model_path or settings.ACTIVE_MODEL_PATH
        if not os.path.exists(path):
            logger.warning(f"[MLRisk] Model not found at {path}. Using rule-based fallback.")
            cls._model_loaded = False
            return False

        try:
            cls._model = joblib.load(path)
            cls._model_loaded = True
            cls._model_version = os.path.basename(path)
            logger.info(f"[MLRisk] Model loaded: {cls._model_version}")
            return True
        except Exception as e:
            logger.error(f"[MLRisk] Failed to load model: {e}")
            cls._model_loaded = False
            return False

    @classmethod
    def build_feature_vector(cls, parameters: List[Dict[str, Any]]) -> np.ndarray:
        """
        Convert a list of clinical parameter dicts into an ordered 15-dim feature vector.
        Missing parameters are filled with 0.0 (neutral/missing sentinel).
        """
        value_map: Dict[str, float] = {}
        for p in parameters:
            name = p.get("param_name") or p.get("name", "")
            val = p.get("value")
            if name in FEATURE_ORDER and val is not None:
                try:
                    value_map[name] = float(val)
                except (TypeError, ValueError):
                    pass  # skip uncastable values

        vector = np.array([value_map.get(name, 0.0) for name in FEATURE_ORDER], dtype=np.float64)
        return vector

    @classmethod
    def predict(cls, feature_vector: np.ndarray) -> Tuple[float, str]:
        """
        Run ML inference on a 15-dim feature vector.
        Returns (risk_score: float, risk_level: str).
        """
        if feature_vector.shape != (15,):
            raise InvalidFeatureVectorError(
                f"Feature vector must be 15-dimensional, got {feature_vector.shape}"
            )

        if cls._model_loaded and cls._model is not None:
            try:
                vec_2d = feature_vector.reshape(1, -1)
                # Support classifiers (predict_proba) or regressors (predict)
                if hasattr(cls._model, "predict_proba"):
                    proba = cls._model.predict_proba(vec_2d)[0]
                    # Assume binary: [P(low), P(high)] or multi-class
                    if len(proba) == 2:
                        risk_score = float(proba[1])
                    else:
                        risk_score = float(np.max(proba))
                else:
                    risk_score = float(cls._model.predict(vec_2d)[0])
                    risk_score = max(0.0, min(1.0, risk_score))

                risk_level = cls._score_to_level(risk_score)
                logger.debug(f"[MLRisk] ML prediction: score={risk_score:.4f} level={risk_level}")
                return risk_score, risk_level
            except Exception as e:
                logger.error(f"[MLRisk] Inference failed, falling back to rule-based: {e}")

        # Rule-based fallback
        return cls._rule_based_score(feature_vector)

    @classmethod
    def _rule_based_score(cls, vector: np.ndarray) -> Tuple[float, str]:
        """
        Rule-based fallback scoring using reference ranges from SUPPORTED_PARAMETERS.
        Each out-of-range parameter contributes to overall risk.
        """
        total = 0.0
        count = 0

        for i, name in enumerate(FEATURE_ORDER):
            val = vector[i]
            if val == 0.0:
                continue  # missing sentinel
            ref = SUPPORTED_PARAMETERS[name]
            ref_min = ref.get("ref_min")
            ref_max = ref.get("ref_max")
            critical = ref.get("critical_threshold")

            if critical and abs(val - critical) < abs(critical * 0.1):
                total += 0.25
            elif ref_min is not None and val < ref_min:
                deviation = (ref_min - val) / ref_min if ref_min != 0 else 0
                total += min(0.15, 0.05 + deviation * 0.10)
            elif ref_max is not None and val > ref_max:
                deviation = (val - ref_max) / ref_max if ref_max != 0 else 0
                total += min(0.15, 0.05 + deviation * 0.10)
            count += 1

        risk_score = min(1.0, round(total, 4)) if count > 0 else 0.0
        risk_level = cls._score_to_level(risk_score)
        logger.debug(f"[MLRisk] Rule-based score: {risk_score:.4f} → {risk_level}")
        return risk_score, risk_level

    @staticmethod
    def _score_to_level(score: float) -> str:
        if score >= RISK_THRESHOLDS["CRITICAL"]:
            return "CRITICAL"
        if score >= RISK_THRESHOLDS["HIGH"]:
            return "HIGH"
        if score >= RISK_THRESHOLDS["MODERATE"]:
            return "MODERATE"
        return "LOW"

    @classmethod
    def compute_risk(cls, parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Full risk computation pipeline:
        1. Build feature vector from parameter list
        2. Run ML inference (or fallback)
        3. Return structured result dict
        """
        if not parameters:
            return {
                "overall_risk": 0.0,
                "risk_level": "LOW",
                "ml_model_used": False,
                "model_version": None,
                "feature_vector": [0.0] * 15,
            }

        feature_vector = cls.build_feature_vector(parameters)
        risk_score, risk_level = cls.predict(feature_vector)

        return {
            "overall_risk": risk_score,
            "risk_level": risk_level,
            "ml_model_used": cls._model_loaded,
            "model_version": cls._model_version,
            "feature_vector": feature_vector.tolist(),
        }
