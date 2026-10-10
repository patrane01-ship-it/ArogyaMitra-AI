"""
ArogyaMitra AI - Prediction Strategy Pattern (Phase 3)
Abstract strategy + linear regression concrete implementation.
Per FEATURES_PHASE3.md §2.3 and §3 F2.
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class PredictionInput:
    """Input data for a prediction computation."""
    profile_id: str
    param_name: str
    readings: list  # list of (datetime, float) tuples sorted oldest first
    threshold_value: float
    threshold_label: str

@dataclass 
class PredictionOutput:
    """Output of a prediction computation."""
    current_value: float
    current_trend: str  # STABLE | IMPROVING | WORSENING | VOLATILE
    slope: float
    months_to_threshold: Optional[int]  # None if no crossing, capped at 36
    confidence: float  # 0-1, derived from R²
    data_points_used: int
    alert_level: str  # NONE | WATCH | WARN | URGENT
    narrative: str

class PredictionStrategy(ABC):
    """Abstract base for prediction algorithms."""
    
    @abstractmethod
    def compute(self, inp: PredictionInput) -> PredictionOutput:
        """Compute prediction from input readings."""
        ...

    @staticmethod
    def determine_alert_level(trend: str, months: Optional[int], confidence: float) -> str:
        if trend in ('STABLE', 'IMPROVING') or trend == 'VOLATILE':
            return 'NONE'
        if months is None:
            return 'NONE'
        if months <= 3:
            return 'URGENT'
        if months <= 9:
            return 'WARN'
        return 'WATCH'

class LinearRegressionStrategy(PredictionStrategy):
    """Linear regression strategy for health trajectory prediction."""
    
    def compute(self, inp: PredictionInput) -> PredictionOutput:
        if not inp.readings or len(inp.readings) < 3:
            return PredictionOutput(
                current_value=inp.readings[-1][1] if inp.readings else 0.0,
                current_trend='VOLATILE',
                slope=0.0,
                months_to_threshold=None,
                confidence=0.0,
                data_points_used=len(inp.readings),
                alert_level='NONE',
                narrative=f"Not enough data to compute trend for {inp.param_name}."
            )
            
        first_date = inp.readings[0][0]
        x_days = np.array([(r[0] - first_date).days for r in inp.readings])
        y_vals = np.array([r[1] for r in inp.readings])
        
        current_value = y_vals[-1]
        data_points_used = len(inp.readings)
        
        slope, intercept = np.polyfit(x_days, y_vals, 1)
        
        y_pred = slope * x_days + intercept
        ss_res = np.sum((y_vals - y_pred) ** 2)
        ss_tot = np.sum((y_vals - np.mean(y_vals)) ** 2)
        
        if ss_tot == 0:
            r_squared = 0.0
            trend = 'VOLATILE'
        else:
            r_squared = 1 - (ss_res / ss_tot)
            trend = 'STABLE'
            
        confidence = float(r_squared)
        threshold_factor = abs(inp.threshold_value) * 0.005
        months_to_threshold = None
        
        if r_squared < 0.40:
            trend = 'VOLATILE'
            confidence = float(r_squared)
        else:
            confidence = min(r_squared, 0.99)
            if slope > threshold_factor:
                trend = 'WORSENING'
            elif slope < -threshold_factor:
                trend = 'IMPROVING'
            else:
                trend = 'STABLE'
                
            if trend == 'WORSENING' and inp.threshold_value > current_value:
                if slope > 0:
                    days = (inp.threshold_value - current_value) / slope
                    months = days / 30.0
                    if months > 0:
                        months_to_threshold = min(int(round(months)), 36)
                        
        if trend in ('STABLE', 'VOLATILE'):
            narrative = f"Your {inp.param_name} has been {trend.lower()} over the past {data_points_used} readings."
        else:
            if months_to_threshold is not None:
                narrative = f"Your {inp.param_name} has been {trend.lower()} over {data_points_used} readings. At the current rate, it may reach {inp.threshold_label} in approximately {months_to_threshold} months."
            else:
                narrative = f"Your {inp.param_name} has been {trend.lower()} over {data_points_used} readings."
                
        alert_level = self.determine_alert_level(trend, months_to_threshold, confidence)
        
        return PredictionOutput(
            current_value=float(current_value),
            current_trend=trend,
            slope=float(slope),
            months_to_threshold=months_to_threshold,
            confidence=float(max(0.0, min(1.0, confidence))),
            data_points_used=data_points_used,
            alert_level=alert_level,
            narrative=narrative
        )
