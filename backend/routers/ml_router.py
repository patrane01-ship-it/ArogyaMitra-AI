"""
ArogyaMitra AI - ML Risk Router (Phase 2)
Endpoints for ML-powered health risk prediction and model management.
Per FEATURES_PHASE2.md §2.2.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from backend.core.dependencies import get_current_user, get_param_repo, get_risk_repo, get_cache
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.repositories.risk_score_repo import RiskScoreRepository
from backend.services.ml_risk_engine import MLRiskEngine
from backend.core.cache import ArogyaCache
from backend.exceptions.arogya_errors import InsufficientDataError
from pydantic import BaseModel


router = APIRouter(prefix="/api/ml", tags=["ML Risk"])


# ── Response Schemas ───────────────────────────────────────────

class MLRiskResponse(BaseModel):
    user_id: str
    overall_risk: float
    risk_level: str
    ml_model_used: bool
    model_version: Optional[str] = None
    feature_vector: List[float]
    recommendation: str


class ModelStatusResponse(BaseModel):
    ml_model_loaded: bool
    model_version: Optional[str]
    fallback_mode: str


# ── Endpoints ──────────────────────────────────────────────────

@router.get("/risk/predict", response_model=MLRiskResponse)
async def predict_risk_ml(
    user_id: str = Depends(get_current_user),
    param_repo: ClinicalParameterRepository = Depends(get_param_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """
    Predict health risk using ML model (or rule-based fallback).
    Uses latest clinical parameters to build a 15-dim feature vector.
    Result is cached for 5 minutes.
    """
    cache_key = f"ml_risk_{user_id}"
    cached = await cache.get("ml_risk", user_id)
    if cached:
        return cached

    params = await param_repo.get_latest_for_user(user_id)
    if not params:
        raise InsufficientDataError("No clinical parameters found. Upload lab reports first.")

    params_dicts = [p.to_dict() for p in params]
    result = MLRiskEngine.compute_risk(params_dicts)

    risk_level = result["risk_level"]
    recommendations = {
        "CRITICAL": "Seek immediate medical attention. Multiple critical parameters detected.",
        "HIGH": "Consult your doctor promptly. Multiple parameters outside normal range.",
        "MODERATE": "Schedule a check-up. Some parameters need monitoring.",
        "LOW": "All parameters are within healthy ranges. Keep up the good work!",
    }

    response = {
        "user_id": user_id,
        "overall_risk": result["overall_risk"],
        "risk_level": risk_level,
        "ml_model_used": result["ml_model_used"],
        "model_version": result["model_version"],
        "feature_vector": result["feature_vector"],
        "recommendation": recommendations.get(risk_level, "Consult a healthcare professional."),
    }

    await cache.set("ml_risk", user_id, response, ttl=300)
    return response


@router.get("/model/status", response_model=ModelStatusResponse)
async def get_model_status(
    user_id: str = Depends(get_current_user),
):
    """
    Get current ML model status.
    """
    return ModelStatusResponse(
        ml_model_loaded=MLRiskEngine._model_loaded,
        model_version=MLRiskEngine._model_version,
        fallback_mode="rule_based" if not MLRiskEngine._model_loaded else "ml_inference",
    )


@router.post("/model/reload")
async def reload_model(
    user_id: str = Depends(get_current_user),
):
    """
    Hot-reload ML model from disk. Used after deploying a new model artifact.
    """
    success = MLRiskEngine.load_model()
    return {
        "success": success,
        "message": (
            f"ML model loaded: {MLRiskEngine._model_version}"
            if success
            else "No model file found. Running in rule-based fallback mode."
        ),
    }
