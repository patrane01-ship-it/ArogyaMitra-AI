"""
ArogyaMitra AI - Subscription Repository
Data access layer for SubscriptionTier entity.
"""

from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.subscription_tier import SubscriptionTier, TIER_DEFAULTS
from backend.exceptions.arogya_errors import DatabaseError
from backend.core.logger import logger

class SubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_subscription(self, user_id: str) -> Optional[SubscriptionTier]:
        try:
            stmt = select(SubscriptionTier).where(
                SubscriptionTier.user_id == user_id,
                SubscriptionTier.is_active.is_(True)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:Subscription] get_active error: {e}")
            raise DatabaseError("Failed to fetch active subscription")

    async def create(self, sub: SubscriptionTier) -> SubscriptionTier:
        try:
            sub.validate()
            self.db.add(sub)
            await self.db.flush()
            await self.db.refresh(sub)
            return sub
        except Exception as e:
            logger.error(f"[Repo:Subscription] Error creating subscription: {e}")
            raise DatabaseError("Failed to create subscription")

    async def update(self, sub: SubscriptionTier) -> SubscriptionTier:
        try:
            sub.validate()
            await self.db.flush()
            await self.db.refresh(sub)
            return sub
        except Exception as e:
            logger.error(f"[Repo:Subscription] update error: {e}")
            raise DatabaseError("Failed to update subscription")

    async def upsert_free(self, user_id: str) -> SubscriptionTier:
        sub = await self.get_active_subscription(user_id)
        if sub:
            return sub
            
        free_sub = SubscriptionTier.create_free(user_id)
        return await self.create(free_sub)

    async def get_tier_limit(self, user_id: str, feature: str) -> Any:
        sub = await self.get_active_subscription(user_id)
        if sub is None:
            if feature == "family_members":
                return TIER_DEFAULTS["FREE"]["family_member_limit"]
            elif feature == "doctor_access":
                return TIER_DEFAULTS["FREE"]["doctor_access_limit"]
            return False
            
        if feature == "family_members":
            return sub.family_member_limit
        elif feature == "doctor_access":
            return sub.doctor_access_limit
            
        return sub.is_feature_available(feature)
