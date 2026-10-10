"""
ArogyaMitra AI - ClinicalParameter Repository
Data access layer for clinical parameters, joined with parent HealthRecord for user_id scoping.
Per PRODUCTION_BACKEND.md §4.2, §6.3 and SECURITY_AUDIT.md §5.
"""

from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from backend.models.clinical_parameter import ClinicalParameter
from backend.models.health_record import HealthRecord
from backend.core.logger import logger
from backend.exceptions.arogya_errors import (
    ArogyaError,
    DatabaseError,
)


class ClinicalParameterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, param: ClinicalParameter) -> ClinicalParameter:
        """Create a single clinical parameter."""
        try:
            param.validate()
            self.db.add(param)
            await self.db.flush()
            return param
        except ArogyaError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:ClinicalParam] Error creating param: {e}")
            raise DatabaseError("Failed to save clinical parameter")

    async def create_many(self, params: List[ClinicalParameter]) -> List[ClinicalParameter]:
        """Bulk create clinical parameters."""
        try:
            for p in params:
                p.validate()
                self.db.add(p)
            await self.db.flush()
            return params
        except ArogyaError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:ClinicalParam] Error in create_many: {e}")
            raise DatabaseError("Failed to save clinical parameters")

    async def get_by_id(self, param_id: str, user_id: str) -> Optional[ClinicalParameter]:
        """Fetch a parameter by ID, ensuring parent record belongs to user and is not deleted."""
        try:
            stmt = (
                select(ClinicalParameter)
                .join(HealthRecord, ClinicalParameter.record_id == HealthRecord.record_id)
                .where(
                    ClinicalParameter.param_id == param_id,
                    HealthRecord.user_id == user_id,
                    HealthRecord.is_deleted.is_(False),
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:ClinicalParam] Error getting param {param_id}: {e}")
            raise DatabaseError("Database error during parameter lookup")

    async def get_latest_for_user(self, user_id: str) -> List[ClinicalParameter]:
        """Fetch the most recent reading for each distinct parameter for a user."""
        try:
            # Query all parameters belonging to non-deleted records of this user
            stmt = (
                select(ClinicalParameter)
                .join(HealthRecord, ClinicalParameter.record_id == HealthRecord.record_id)
                .where(
                    HealthRecord.user_id == user_id,
                    HealthRecord.is_deleted.is_(False),
                )
                .order_by(ClinicalParameter.report_date.desc())
            )
            result = await self.db.execute(stmt)
            all_params = list(result.scalars().all())

            # Filter for most recent reading per parameter name
            latest_map: Dict[str, ClinicalParameter] = {}
            for p in all_params:
                if p.param_name not in latest_map:
                    latest_map[p.param_name] = p

            return list(latest_map.values())
        except Exception as e:
            logger.error(f"[Repo:ClinicalParam] Error fetching latest params for {user_id}: {e}")
            raise DatabaseError("Failed to fetch clinical parameters")

    async def get_history_for_param(
        self, param_name: str, user_id: str
    ) -> List[ClinicalParameter]:
        """Fetch historical readings for a parameter name sorted ascending by report date."""
        try:
            stmt = (
                select(ClinicalParameter)
                .join(HealthRecord, ClinicalParameter.record_id == HealthRecord.record_id)
                .where(
                    ClinicalParameter.param_name == param_name,
                    HealthRecord.user_id == user_id,
                    HealthRecord.is_deleted.is_(False),
                )
                .order_by(ClinicalParameter.report_date.asc())
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"[Repo:ClinicalParam] Error getting history for {param_name}: {e}")
            raise DatabaseError("Failed to fetch parameter history")

    async def update_value(
        self, param_id: str, user_id: str, value: float, unit: str
    ) -> Optional[ClinicalParameter]:
        """Update value and unit of a parameter, recomputing its status."""
        param = await self.get_by_id(param_id, user_id)
        if not param:
            return None

        param.value = value
        param.unit = unit
        param.validate()  # Recomputes status

        try:
            await self.db.flush()
            return param
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:ClinicalParam] Error updating parameter {param_id}: {e}")
            raise DatabaseError("Failed to update parameter value")
