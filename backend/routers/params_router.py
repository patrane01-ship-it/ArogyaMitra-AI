"""
ArogyaMitra AI - Clinical Parameters Router
Endpoints for reading latest clinical parameters, parameter timelines, and manual correction.
Per PRODUCTION_BACKEND.md §10.3.
"""

import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from backend.core.cache import ArogyaCache
from backend.core.dependencies import (
    get_current_user,
    get_param_repo,
    get_cache,
)
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.schemas.clinical_parameter_schema import (
    ClinicalParameterResponse,
    ClinicalParameterUpdate,
    ParameterHistoryResponse,
    ParameterHistoryPoint,
)
from backend.config import SUPPORTED_PARAMETERS
from backend.exceptions.arogya_errors import ArogyaError, RecordNotFoundError
from backend.agents.graph import run_pipeline

router = APIRouter(prefix="/api/params", tags=["Parameters"])


@router.get("/", response_model=List[ClinicalParameterResponse])
async def get_latest_parameters(
    user_id: str = Depends(get_current_user),
    param_repo: ClinicalParameterRepository = Depends(get_param_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """
    Get latest reading for each tracked clinical parameter.
    Cached for 3 minutes.
    """
    cached = await cache.get("clinical_params", user_id)
    if cached is not None:
        return cached

    params = await param_repo.get_latest_for_user(user_id)
    data = [p.to_dict() for p in params]
    await cache.set("clinical_params", user_id, data)
    return data


@router.get("/{param_name}", response_model=ParameterHistoryResponse)
async def get_parameter_history(
    param_name: str,
    user_id: str = Depends(get_current_user),
    param_repo: ClinicalParameterRepository = Depends(get_param_repo),
):
    """
    Get full chronological history for a specific parameter (for Recharts timeline).
    """
    history = await param_repo.get_history_for_param(param_name, user_id)
    if not history:
        raise RecordNotFoundError(f"No recorded data found for parameter '{param_name}'")

    config = SUPPORTED_PARAMETERS.get(param_name, {})
    default_unit = history[0].unit if history else config.get("unit", "")
    ref_min = history[0].reference_range_min or config.get("ref_min")
    ref_max = history[0].reference_range_max or config.get("ref_max")

    readings = [
        ParameterHistoryPoint(
            value=h.value,
            report_date=h.report_date,
            status=h.status,
            anomaly_score=h.anomaly_score,
        )
        for h in history
    ]

    return ParameterHistoryResponse(
        param_name=param_name,
        unit=default_unit,
        reference_range_min=ref_min,
        reference_range_max=ref_max,
        readings=readings,
    )


@router.put("/{param_id}", response_model=ClinicalParameterResponse)
async def update_parameter(
    param_id: str,
    payload: ClinicalParameterUpdate,
    user_id: str = Depends(get_current_user),
    param_repo: ClinicalParameterRepository = Depends(get_param_repo),
    cache: ArogyaCache = Depends(get_cache),
):
    """
    Manually correct an extracted parameter value.
    Re-evaluates threshold status and triggers trend risk recomputation.
    """
    updated = await param_repo.update_value(
        param_id=param_id,
        user_id=user_id,
        value=payload.value,
        unit=payload.unit,
    )
    if not updated:
        raise RecordNotFoundError(f"Parameter {param_id} not found")

    # Invalidate caches
    await cache.invalidate("clinical_params", user_id)
    await cache.invalidate("risk_score", user_id)

    # Trigger background recomputation of overall risk
    asyncio.create_task(
        run_pipeline(
            record_id=updated.record_id,
            user_id=user_id,
            record_type="MANUAL_ENTRY",
        )
    )

    return updated
