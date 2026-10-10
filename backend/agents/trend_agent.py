"""
ArogyaMitra AI - Trend Agent
LangGraph node: Analyzes historical and recent clinical parameters, calculates overall health risk,
and saves the updated RiskScore.
Per TECH_STACK.md §3 and FEATURES.md §3 (Feature 3).
"""

from typing import Dict, Any
from datetime import datetime, timezone
from backend.core.logger import logger
from backend.services.risk_engine import RiskEngine
from backend.models.risk_score import RiskScore
from backend.database import get_async_session_factory
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.repositories.risk_score_repo import RiskScoreRepository


async def trend_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Trend Agent node in LangGraph state machine."""
    record_id = state.get("record_id", "")
    user_id = state.get("user_id", "local_user")

    logger.info(f"[Agent:TrendAgent] START | record_id={record_id} | user_id={user_id}")
    state["current_step"] = "trend_running"

    try:
        async_factory = get_async_session_factory()
        async with async_factory() as session:
            param_repo = ClinicalParameterRepository(session)
            risk_repo = RiskScoreRepository(session)

            # Fetch all latest parameters for user across all non-deleted records
            latest_params = await param_repo.get_latest_for_user(user_id)
            params_dict_list = [p.to_dict() for p in latest_params]

            # Calculate risk using rule engine
            overall_risk, risk_level, factors, recs = RiskEngine.calculate_risk(params_dict_list)

            # Persist RiskScore
            risk_model = RiskScore(
                user_id=user_id,
                computed_at=datetime.now(timezone.utc),
                overall_risk=overall_risk,
                risk_level=risk_level,
                contributing_factors=factors,
                recommendations=recs,
            )
            await risk_repo.create(risk_model)
            await session.commit()

            state["risk_score"] = overall_risk
            state["risk_level"] = risk_level
            state["current_step"] = "trend_success"

            logger.info(
                f"[Agent:TrendAgent] DONE | record_id={record_id} | risk={overall_risk} ({risk_level})"
            )

    except Exception as e:
        logger.exception(f"[Agent:TrendAgent] FAIL | record_id={record_id} | {type(e).__name__}: {e}")
        state["errors"].append({"agent": "trend", "error": "UNEXPECTED", "message": str(e)})
        state["current_step"] = "trend_failed"

    return state
