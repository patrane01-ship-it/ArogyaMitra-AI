"""
ArogyaMitra AI - Prediction Repository (Phase 3)
Data access layer for prediction results.
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.prediction_result import PredictionResult
from backend.exceptions.arogya_errors import RecordNotFoundError


class PredictionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, result: PredictionResult) -> PredictionResult:
        self.db.add(result)
        await self.db.flush()
        await self.db.refresh(result)
        return result

    async def get_latest(self, profile_id: str, param_name: str) -> Optional[PredictionResult]:
        stmt = (
            select(PredictionResult)
            .where(
                PredictionResult.profile_id == profile_id,
                PredictionResult.param_name == param_name
            )
            .order_by(PredictionResult.computed_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_profile(self, profile_id: str, limit: int = 20) -> List[PredictionResult]:
        stmt = (
            select(PredictionResult)
            .where(PredictionResult.profile_id == profile_id)
            .order_by(PredictionResult.computed_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, prediction_id: str, profile_id: str) -> PredictionResult:
        stmt = (
            select(PredictionResult)
            .where(
                PredictionResult.prediction_id == prediction_id,
                PredictionResult.profile_id == profile_id
            )
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            raise RecordNotFoundError("Prediction result not found")
        return record
