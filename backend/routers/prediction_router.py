"""
ArogyaMitra AI - Prediction Router (Phase 3)
Exposes prediction API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from backend.services.prediction_service import PredictionService
from backend.core.dependencies import get_current_user, require_tier, get_prediction_service
from backend.exceptions.arogya_errors import ArogyaError

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

class RunPredictionRequest(BaseModel):
    param_name: str
    profile_id: Optional[str] = None

@router.post("/run")
async def run_prediction(
    request: RunPredictionRequest,
    user_id: str = Depends(get_current_user),
    _: None = Depends(require_tier("PREMIUM")),
    service: PredictionService = Depends(get_prediction_service)
):
    target_profile = request.profile_id or user_id
    try:
        result = await service.run_prediction(target_profile, request.param_name)
        return {"prediction": result.to_dict()}
    except ArogyaError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to run prediction")

@router.get("/{param_name}")
async def get_latest_prediction(
    param_name: str,
    profile_id: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user),
    _: None = Depends(require_tier("PREMIUM")),
    service: PredictionService = Depends(get_prediction_service)
):
    target_profile = profile_id or user_id
    result = await service.get_latest(target_profile, param_name)
    if not result:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {"prediction": result.to_dict()}

@router.get("/")
async def list_predictions(
    profile_id: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user),
    _: None = Depends(require_tier("PREMIUM")),
    service: PredictionService = Depends(get_prediction_service)
):
    target_profile = profile_id or user_id
    results = await service.list_predictions(target_profile)
    return {"predictions": [r.to_dict() for r in results]}
