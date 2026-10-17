"""
ArogyaMitra AI - Phase 4 Model Governance & Drift Detection Service
Calculates Population Stability Index (PSI) and handles Shadow model evaluation.
Per PHASE4_IMPLEMENTATION.md F8.
"""

import math
from typing import List, Dict, Any, Tuple
from backend.core.logger import logger


class ModelGovernanceService:
    """Service providing model explainability, drift detection (PSI), and shadow monitoring."""

    @staticmethod
    def calculate_psi(expected: List[float], actual: List[float], num_buckets: int = 10) -> float:
        """
        Calculates Population Stability Index (PSI) to detect data or feature distribution drift.
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Moderate drift
        PSI >= 0.2: Significant drift detected (triggers alert)
        """
        if not expected or not actual:
            return 0.0

        min_val = min(min(expected), min(actual))
        max_val = max(max(expected), max(actual))

        if min_val == max_val:
            return 0.0

        step = (max_val - min_val) / num_buckets
        breakpoints = [min_val + i * step for i in range(1, num_buckets)]

        def get_counts(data: List[float]) -> List[int]:
            counts = [0] * num_buckets
            for val in data:
                placed = False
                for i, bp in enumerate(breakpoints):
                    if val <= bp:
                        counts[i] += 1
                        placed = True
                        break
                if not placed:
                    counts[-1] += 1
            return counts

        exp_counts = get_counts(expected)
        act_counts = get_counts(actual)

        exp_total = len(expected)
        act_total = len(actual)

        psi = 0.0
        for e_cnt, a_cnt in zip(exp_counts, act_counts):
            # Smooth with small epsilon to avoid division by zero
            e_pct = (e_cnt + 0.0001) / exp_total
            a_pct = (a_cnt + 0.0001) / act_total

            psi += (a_pct - e_pct) * math.log(a_pct / e_pct)

        return round(psi, 4)

    @classmethod
    def evaluate_drift(cls, baseline_data: Dict[str, List[float]], current_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """Evaluates PSI across all clinical features and flags any exceeding threshold 0.2."""
        feature_psi = {}
        alert_features = []

        for feature, baseline_vals in baseline_data.items():
            current_vals = current_data.get(feature, [])
            if baseline_vals and current_vals:
                psi_val = cls.calculate_psi(baseline_vals, current_vals)
                feature_psi[feature] = psi_val
                if psi_val >= 0.2:
                    alert_features.append(feature)

        return {
            "feature_psi": feature_psi,
            "has_drift": len(alert_features) > 0,
            "alert_features": alert_features
        }
