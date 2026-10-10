"""
ArogyaMitra AI - Risk Router
Endpoints for health risk score gauge, contributing factors, historical trends, and recomputation.
Per PRODUCTION_BACKEND.md §10.4.
"""

from typing import List, Union
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from backend.core.cache import ArogyaCache
from backend.core.dependencies import (
    get_current_user,
    get_risk_repo,
    get_param_repo,
    get_cache,
)
from backend.repositories.risk_score_repo import RiskScoreRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.services.risk_engine import RiskEngine
from backend.models.risk_score import RiskScore
from backend.schemas.risk_score_schema import (
    RiskScoreResponse,
    RiskScoreNoDataResponse,
)
from backend.exceptions.arogya_errors import InsufficientDataError

router = APIRouter(prefix="/api/risk", tags=["Risk"])


@router.get("/current", response_model=Union[RiskScoreResponse, RiskScoreNoDataResponse])
async def get_current_risk(
    user_id: str = Depends(get_current_user),
    risk_repo: RiskScoreRepository = Depends(get_risk_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """
    Get latest health risk score.
    Cached for 5 minutes.
    """
    cached = await cache.get("risk_score", user_id)
    if cached is not None:
        return cached

    latest = await risk_repo.get_latest(user_id)
    if not latest:
        return RiskScoreNoDataResponse()

    data = latest.to_dict()
    await cache.set("risk_score", user_id, data)
    return data


@router.get("/history", response_model=List[RiskScoreResponse])
async def get_risk_history(
    limit: int = 20,
    user_id: str = Depends(get_current_user),
    risk_repo: RiskScoreRepository = Depends(get_risk_repo),
):
    """Get chronological risk score history."""
    return await risk_repo.get_history(user_id=user_id, limit=limit)


@router.post("/recompute", response_model=RiskScoreResponse)
async def recompute_risk(
    user_id: str = Depends(get_current_user),
    param_repo: ClinicalParameterRepository = Depends(get_param_repo),
    risk_repo: RiskScoreRepository = Depends(get_risk_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """
    Synchronously recompute health risk assessment from latest clinical parameters.
    """
    latest_params = await param_repo.get_latest_for_user(user_id)
    if not latest_params:
        raise InsufficientDataError("No clinical parameters found to compute risk score")

    params_dict_list = [p.to_dict() for p in latest_params]
    overall_risk, risk_level, factors, recs = RiskEngine.calculate_risk(params_dict_list)

    score = RiskScore(
        user_id=user_id,
        computed_at=datetime.now(timezone.utc),
        overall_risk=overall_risk,
        risk_level=risk_level,
        contributing_factors=factors,
        recommendations=recs,
    )
    saved = await risk_repo.create(score)
    await cache.invalidate("risk_score", user_id)

    return saved
