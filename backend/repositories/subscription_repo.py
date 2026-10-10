"""
ArogyaMitra AI - Subscription Repository (Phase 3)
Data access layer for SubscriptionTier entity.
Per FEATURES_PHASE3.md §2.5.
"""

from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.subscription_tier import SubscriptionTier, TIER_DEFAULTS
from backend.core.logger import logger
from backend.exceptions.arogya_errors import DatabaseError, SubscriptionNotFoundError


class SubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_user(self, user_id: str) -> Optional[SubscriptionTier]:
        """Get current subscription for user. Returns None if not found."""
        try:
            stmt = select(SubscriptionTier).where(
                SubscriptionTier.user_id == user_id,
                SubscriptionTier.is_active.is_(True),
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:Subscription] get_for_user error: {e}")
            raise DatabaseError("Failed to fetch subscription")

    async def get_or_create_free(self, user_id: str) -> SubscriptionTier:
        """Get subscription, creating a FREE tier if it doesn't exist."""
        sub = await self.get_for_user(user_id)
        if sub:
            return sub
        free_sub = SubscriptionTier.create_free(user_id)
        self.db.add(free_sub)
        await self.db.flush()
        logger.info(f"[Subscription] Created FREE tier for user_id={user_id}")
        return free_sub

    async def upgrade(
        self,
        user_id: str,
        tier: str,
        months: int = 1,
        payment_reference: str = None,
    ) -> SubscriptionTier:
        """Upgrade user to PREMIUM or PRO tier."""
        if tier not in TIER_DEFAULTS:
            raise ValueError(f"Invalid tier: {tier}")

        sub = await self.get_for_user(user_id)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=30 * months)
        defaults = TIER_DEFAULTS[tier]

        if sub:
            sub.tier = tier
            sub.expires_at = expires_at
            sub.payment_reference = payment_reference
            sub.is_active = True
            for key, val in defaults.items():
                setattr(sub, key, val)
        else:
            sub = SubscriptionTier(
                user_id=user_id,
                tier=tier,
                started_at=now,
                expires_at=expires_at,
                payment_reference=payment_reference,
                **defaults,
            )
            self.db.add(sub)

        await self.db.flush()
        logger.info(f"[Subscription] Upgraded user_id={user_id} to {tier} (expires: {expires_at})")
        return sub

    async def downgrade_to_free(self, user_id: str) -> SubscriptionTier:
        """Downgrade user to FREE tier (data preserved)."""
        sub = await self.get_for_user(user_id)
        if not sub:
            sub = SubscriptionTier.create_free(user_id)
            self.db.add(sub)
        else:
            defaults = TIER_DEFAULTS["FREE"]
            sub.tier = "FREE"
            sub.expires_at = None
            sub.payment_reference = None
            for key, val in defaults.items():
                setattr(sub, key, val)
        await self.db.flush()
        return sub

    async def check_feature(self, user_id: str, feature: str) -> bool:
        """Check if user's subscription allows a given feature."""
        sub = await self.get_for_user(user_id)
        if not sub:
            return False  # No subscription → treat as expired FREE
        if sub.is_expired():
            return False
        return sub.is_feature_available(feature)
