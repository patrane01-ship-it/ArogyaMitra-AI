"""
ArogyaMitra AI - Anomaly Detection Service (Phase 2)
IsolationForest-based anomaly detection for time-series clinical parameter trends.
Per FEATURES_PHASE2.md §2.3 and TECH_STACK_PHASE2.md §4.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from sklearn.ensemble import IsolationForest

from backend.config import settings
from backend.core.logger import logger
from backend.exceptions.arogya_errors import (
    InsufficientDataForAnomalyError,
    InsufficientVarianceError,
    InvalidContaminationError,
)

_MIN_READINGS = 3


class AnomalyDetectionService:
    """
    Detects anomalous readings in a time-series of clinical parameter values.
    Uses IsolationForest with configurable contamination factor.
    Falls back to z-score based detection if fewer than MIN_READINGS.
    """

    @staticmethod
    def _validate_inputs(readings: List[float], contamination: float) -> None:
        """Validate input constraints."""
        if len(readings) < _MIN_READINGS:
            raise InsufficientDataForAnomalyError(
                f"At least {_MIN_READINGS} readings required for anomaly detection, got {len(readings)}"
            )
        if not (0.01 <= contamination <= 0.5):
            raise InvalidContaminationError()

    @staticmethod
    def _check_variance(readings: List[float]) -> float:
        """Return variance; raise error if near-zero."""
        arr = np.array(readings, dtype=np.float64)
        variance = float(np.var(arr))
        if variance < 1e-8:
            raise InsufficientVarianceError(
                "All readings are identical — cannot perform anomaly detection"
            )
        return variance

    @staticmethod
    def detect_isolation_forest(
        readings: List[float],
        timestamps: Optional[List[str]] = None,
        contamination: float = None,
    ) -> List[Dict[str, Any]]:
        """
        Run IsolationForest anomaly detection on a list of float values.
        Returns a list of result dicts, one per reading, with anomaly label and score.

        Args:
            readings: List of float values (e.g., HbA1c values over time)
            timestamps: Optional list of ISO timestamp strings (same length as readings)
            contamination: Fraction of expected anomalies (default: settings.ANOMALY_CONTAMINATION)

        Returns:
            [{"value": float, "timestamp": str|None, "is_anomaly": bool, "anomaly_score": float}]
        """
        contamination = contamination or settings.ANOMALY_CONTAMINATION
        AnomalyDetectionService._validate_inputs(readings, contamination)
        AnomalyDetectionService._check_variance(readings)

        arr = np.array(readings, dtype=np.float64).reshape(-1, 1)

        model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
        )
        model.fit(arr)

        labels = model.predict(arr)  # 1 = normal, -1 = anomaly
        scores = model.score_samples(arr)  # lower = more anomalous

        results = []
        for i, (val, label, score) in enumerate(zip(readings, labels, scores)):
            ts = timestamps[i] if timestamps and i < len(timestamps) else None
            results.append({
                "index": i,
                "value": float(val),
                "timestamp": ts,
                "is_anomaly": bool(label == -1),
                "anomaly_score": round(float(score), 6),
            })

        anomaly_count = sum(1 for r in results if r["is_anomaly"])
        logger.info(
            f"[Anomaly] Detected {anomaly_count}/{len(readings)} anomalies "
            f"(contamination={contamination})"
        )
        return results

    @staticmethod
    def detect_zscore(
        readings: List[float],
        timestamps: Optional[List[str]] = None,
        threshold: float = 2.5,
    ) -> List[Dict[str, Any]]:
        """
        Z-score based anomaly detection (simpler fallback for small datasets).
        A reading is anomalous if |z-score| > threshold.
        """
        if len(readings) < 2:
            raise InsufficientDataForAnomalyError(
                "At least 2 readings required for z-score anomaly detection"
            )

        arr = np.array(readings, dtype=np.float64)
        mean = np.mean(arr)
        std = np.std(arr)

        results = []
        for i, val in enumerate(readings):
            z = float((val - mean) / std) if std > 1e-8 else 0.0
            ts = timestamps[i] if timestamps and i < len(timestamps) else None
            results.append({
                "index": i,
                "value": float(val),
                "timestamp": ts,
                "is_anomaly": abs(z) > threshold,
                "anomaly_score": round(z, 6),
                "z_score": round(z, 4),
            })
        return results

    @classmethod
    def analyze_parameter_trend(
        cls,
        param_name: str,
        readings: List[Dict[str, Any]],
        contamination: float = None,
    ) -> Dict[str, Any]:
        """
        High-level interface: analyze a list of clinical parameter readings for anomalies.

        Args:
            param_name: Name of the clinical parameter (e.g., "HbA1c")
            readings: List of dicts with keys: value (float), recorded_at (str ISO)
            contamination: Optional override for IsolationForest contamination

        Returns:
            {
                "param_name": str,
                "total_readings": int,
                "anomaly_count": int,
                "anomaly_percentage": float,
                "method": "isolation_forest"|"zscore",
                "results": [...]
            }
        """
        if not readings:
            return {
                "param_name": param_name,
                "total_readings": 0,
                "anomaly_count": 0,
                "anomaly_percentage": 0.0,
                "method": "none",
                "results": [],
            }

        values = [float(r.get("value", 0)) for r in readings]
        timestamps = [r.get("recorded_at") or r.get("timestamp") for r in readings]
        contamination = contamination or settings.ANOMALY_CONTAMINATION

        if len(values) >= _MIN_READINGS:
            try:
                results = cls.detect_isolation_forest(values, timestamps, contamination)
                method = "isolation_forest"
            except (InsufficientVarianceError, Exception) as e:
                logger.warning(f"[Anomaly] IsolationForest failed for {param_name}, using z-score: {e}")
                results = cls.detect_zscore(values, timestamps)
                method = "zscore_fallback"
        else:
            results = cls.detect_zscore(values, timestamps)
            method = "zscore"

        anomaly_count = sum(1 for r in results if r["is_anomaly"])
        return {
            "param_name": param_name,
            "total_readings": len(results),
            "anomaly_count": anomaly_count,
            "anomaly_percentage": round(anomaly_count / len(results) * 100, 1),
            "method": method,
            "results": results,
        }
