"""
ArogyaMitra AI - Prediction Service (Phase 3)
Orchestrates health trajectory prediction for a clinical parameter.
Per FEATURES_PHASE3.md §3 F2 and PRODUCTION_BACKEND.md §7, §8.
"""
from typing import Optional, List
from backend.repositories.prediction_repo import PredictionRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.patterns.prediction_strategy import (
    PredictionStrategy,
    LinearRegressionStrategy,
    PredictionInput,
    PredictionOutput
)
from backend.models.prediction_result import PredictionResult
from backend.config import SUPPORTED_PARAMETERS
from backend.exceptions.arogya_errors import InsufficientDataForPredictionError
from backend.core.sanitizer import sanitize_string
from backend.core.guardrails import apply_output_guardrails


class PredictionService:
    def __init__(
        self,
        prediction_repo: PredictionRepository,
        param_repo: ClinicalParameterRepository,
        strategy: Optional[PredictionStrategy] = None,
    ):
        self.prediction_repo = prediction_repo
        self.param_repo = param_repo
        self.strategy = strategy or LinearRegressionStrategy()

    async def run_prediction(self, profile_id: str, param_name: str) -> PredictionResult:
        # Fetch parameter history for the specific parameter and profile_id (maps to user_id in pre-Phase-3 migration)
        readings_models = await self.param_repo.get_history_for_param(param_name, profile_id)
        
        if len(readings_models) < 3:
            raise InsufficientDataForPredictionError()
            
        readings_models.sort(key=lambda r: r.report_date)
        readings = [(r.report_date, r.value) for r in readings_models]
        
        current_value = readings[-1][1]
        
        param_config = SUPPORTED_PARAMETERS.get(param_name)
        if param_config and param_config.get("critical_threshold") is not None:
            threshold_value = float(param_config["critical_threshold"])
            threshold_label = "Upper limit"
        else:
            threshold_value = float(current_value * 1.5)
            threshold_label = "Upper limit"
            
        inp = PredictionInput(
            profile_id=profile_id,
            param_name=param_name,
            readings=readings,
            threshold_value=threshold_value,
            threshold_label=threshold_label
        )
        
        output: PredictionOutput = self.strategy.compute(inp)
        
        raw_narrative = sanitize_string(output.narrative)
        try:
            safe_narrative = apply_output_guardrails(raw_narrative, context="prediction")
        except Exception:
            safe_narrative = f"Your {param_name} trend data has been analyzed. Please consult your doctor for interpretation."
            
        result = PredictionResult(
            profile_id=profile_id,
            param_name=param_name,
            current_value=output.current_value,
            current_trend=output.current_trend,
            slope=output.slope,
            months_to_threshold=output.months_to_threshold,
            threshold_value=inp.threshold_value,
            threshold_label=inp.threshold_label,
            confidence=output.confidence,
            data_points_used=output.data_points_used,
            alert_level=output.alert_level,
            narrative=safe_narrative
        )
        
        saved_result = await self.prediction_repo.save(result)
        return saved_result

    async def get_latest(self, profile_id: str, param_name: str) -> Optional[PredictionResult]:
        return await self.prediction_repo.get_latest(profile_id, param_name)

    async def list_predictions(self, profile_id: str) -> List[PredictionResult]:
        return await self.prediction_repo.list_for_profile(profile_id)
