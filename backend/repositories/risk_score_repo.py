"""
ArogyaMitra AI - RiskScore Repository
Data access layer for RiskScore with user_id scoping and automatic version tracking.
Per PRODUCTION_BACKEND.md §4.2, §6.3 and SECURITY_AUDIT.md §5.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from backend.models.risk_score import RiskScore
from backend.core.logger import logger
from backend.exceptions.arogya_errors import ArogyaError, DatabaseError


class RiskScoreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, score: RiskScore) -> RiskScore:
        """Create a new risk score, automatically determining the version number."""
        try:
            latest = await self.get_latest(score.user_id)
            if latest:
                score.version = latest.version + 1
            else:
                score.version = 1

            score.validate()
            self.db.add(score)
            await self.db.flush()
            return score
        except ArogyaError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:RiskScore] Error saving risk score: {e}")
            raise DatabaseError("Failed to save computed risk score")

    async def get_latest(self, user_id: str) -> Optional[RiskScore]:
        """Fetch the most recent risk score for a user."""
        try:
            stmt = (
                select(RiskScore)
                .where(RiskScore.user_id == user_id)
                .order_by(RiskScore.computed_at.desc())
                .limit(1)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:RiskScore] Error getting latest risk score: {e}")
            raise DatabaseError("Failed to fetch current risk score")

    async def get_history(self, user_id: str, limit: int = 20) -> List[RiskScore]:
        """Fetch historical risk scores for a user, sorted descending by computed date."""
        try:
            limit = min(limit, 100)
            stmt = (
                select(RiskScore)
                .where(RiskScore.user_id == user_id)
                .order_by(RiskScore.computed_at.desc())
                .limit(limit)
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"[Repo:RiskScore] Error getting risk history: {e}")
            raise DatabaseError("Failed to fetch risk score history")
