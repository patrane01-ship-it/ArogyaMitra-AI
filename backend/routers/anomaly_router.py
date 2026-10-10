"""
ArogyaMitra AI - Anomaly Detection Router (Phase 2)
Endpoints for time-series anomaly detection on clinical parameters.
Per FEATURES_PHASE2.md §2.3.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.core.dependencies import get_current_user, get_param_repo
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.services.anomaly_service import AnomalyDetectionService
from backend.exceptions.arogya_errors import (
    InsufficientDataError,
    InsufficientDataForAnomalyError,
)

router = APIRouter(prefix="/api/anomaly", tags=["Anomaly Detection"])


# ── Response schemas ──────────────────────────────────────────

class AnomalyPointResult(BaseModel):
    index: int
    value: float
    timestamp: Optional[str] = None
    is_anomaly: bool
    anomaly_score: float


class AnomalyAnalysisResponse(BaseModel):
    param_name: str
    total_readings: int
    anomaly_count: int
    anomaly_percentage: float
    method: str
    results: List[AnomalyPointResult]


class AllParamsAnomalyResponse(BaseModel):
    user_id: str
    parameters_analyzed: int
    analyses: List[AnomalyAnalysisResponse]


# ── Endpoints ─────────────────────────────────────────────────

@router.get("/parameter/{param_name}", response_model=AnomalyAnalysisResponse)
async def detect_parameter_anomalies(
    param_name: str,
    limit: int = Query(default=50, ge=5, le=200, description="Max historical readings to analyze"),
    contamination: float = Query(default=None, ge=0.01, le=0.5, description="IsolationForest contamination"),
    user_id: str = Depends(get_current_user),
    param_repo: ClinicalParameterRepository = Depends(get_param_repo),
):
    """
    Detect anomalies in a specific clinical parameter's historical trend.
    Returns per-reading anomaly labels using IsolationForest.
    """
    history = await param_repo.get_history_for_param(
        param_name=param_name,
        user_id=user_id,
    )

    if not history:
        raise InsufficientDataError(f"No readings found for parameter '{param_name}'")

    readings = [
        {
            "value": float(r.get("value", 0) if isinstance(r, dict) else r.value),
            "recorded_at": (
                r.get("recorded_at") if isinstance(r, dict) else
                (r.recorded_at.isoformat() if hasattr(r, "recorded_at") and r.recorded_at else None)
            ),
        }
        for r in history
    ]

    result = AnomalyDetectionService.analyze_parameter_trend(
        param_name=param_name,
        readings=readings,
        contamination=contamination,
    )
    return result


@router.get("/all", response_model=AllParamsAnomalyResponse)
async def detect_all_parameter_anomalies(
    limit_per_param: int = Query(default=30, ge=5, le=100),
    user_id: str = Depends(get_current_user),
    param_repo: ClinicalParameterRepository = Depends(get_param_repo),
):
    """
    Run anomaly detection across all tracked clinical parameters for the user.
    Returns a summary with anomaly counts per parameter.
    """
    # Get distinct parameter names
    all_params = await param_repo.get_latest_for_user(user_id)
    if not all_params:
        raise InsufficientDataError("No clinical parameters found for anomaly analysis")

    unique_names = list({
        (p.param_name if hasattr(p, "param_name") else p.get("param_name"))
        for p in all_params
    })

    analyses = []
    for name in unique_names:
        if not name:
            continue
        history = await param_repo.get_history_for_param(param_name=name, user_id=user_id)
        if not history:
            continue

        readings = [
            {
                "value": float(r.get("value", 0) if isinstance(r, dict) else r.value),
                "recorded_at": (
                    r.get("recorded_at") if isinstance(r, dict) else
                    (r.recorded_at.isoformat() if hasattr(r, "recorded_at") and r.recorded_at else None)
                ),
            }
            for r in history
        ]

        try:
            result = AnomalyDetectionService.analyze_parameter_trend(name, readings)
            analyses.append(result)
        except Exception:
            pass  # Skip parameters with insufficient data

    return AllParamsAnomalyResponse(
        user_id=user_id,
        parameters_analyzed=len(analyses),
        analyses=analyses,
    )
