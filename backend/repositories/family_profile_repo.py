"""
ArogyaMitra AI - FamilyProfile Repository (Phase 3)
Data access layer for FamilyProfile entity.
Per FEATURES_PHASE3.md §2.1.
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.family_profile import FamilyProfile
from backend.core.logger import logger
from backend.exceptions.arogya_errors import (
    DatabaseError,
    FamilyProfileNotFoundError,
    CannotDeletePrimaryProfileError,
)

class FamilyProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, profile: FamilyProfile) -> FamilyProfile:
        try:
            profile.validate()
            self.db.add(profile)
            await self.db.flush()
            await self.db.refresh(profile)
            return profile
        except Exception as e:
            logger.error(f"[Repo:FamilyProfile] Error creating profile: {e}")
            raise DatabaseError("Failed to create family profile")

    async def get_by_id(self, profile_id: str, owner_user_id: str) -> FamilyProfile:
        try:
            stmt = select(FamilyProfile).where(
                FamilyProfile.profile_id == profile_id,
                FamilyProfile.owner_user_id == owner_user_id,
                FamilyProfile.is_active.is_(True),
            )
            result = await self.db.execute(stmt)
            profile = result.scalar_one_or_none()
            if not profile:
                raise FamilyProfileNotFoundError()
            return profile
        except FamilyProfileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[Repo:FamilyProfile] get_by_id error: {e}")
            raise DatabaseError("Database error during profile lookup")

    async def get_self_profile(self, owner_user_id: str) -> FamilyProfile:
        try:
            stmt = select(FamilyProfile).where(
                FamilyProfile.owner_user_id == owner_user_id,
                FamilyProfile.is_primary.is_(True),
                FamilyProfile.is_active.is_(True),
            )
            result = await self.db.execute(stmt)
            profile = result.scalar_one_or_none()
            if not profile:
                raise FamilyProfileNotFoundError("Primary profile not found")
            return profile
        except FamilyProfileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[Repo:FamilyProfile] get_self_profile error: {e}")
            raise DatabaseError("Failed to fetch primary profile")

    async def list_by_owner(self, owner_user_id: str) -> list[FamilyProfile]:
        try:
            stmt = select(FamilyProfile).where(
                FamilyProfile.owner_user_id == owner_user_id,
                FamilyProfile.is_active.is_(True),
            ).order_by(FamilyProfile.created_at.asc())
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"[Repo:FamilyProfile] list_by_owner error: {e}")
            raise DatabaseError("Failed to fetch family profiles")

    async def count_active(self, owner_user_id: str) -> int:
        try:
            stmt = select(func.count()).select_from(FamilyProfile).where(
                FamilyProfile.owner_user_id == owner_user_id,
                FamilyProfile.is_active.is_(True),
            )
            result = await self.db.execute(stmt)
            return result.scalar_one() or 0
        except Exception as e:
            logger.error(f"[Repo:FamilyProfile] count error: {e}")
            return 0

    async def update(self, profile: FamilyProfile) -> FamilyProfile:
        try:
            profile.validate()
            await self.db.flush()
            await self.db.refresh(profile)
            return profile
        except Exception as e:
            logger.error(f"[Repo:FamilyProfile] update error: {e}")
            raise DatabaseError("Failed to update family profile")

    async def deactivate(self, profile_id: str, owner_user_id: str) -> FamilyProfile:
        profile = await self.get_by_id(profile_id, owner_user_id)
        if profile.is_primary:
            raise CannotDeletePrimaryProfileError()
        profile.is_active = False
        await self.db.flush()
        return profile

    async def get_profile_for_request(
        self, profile_id: Optional[str], owner_user_id: str
    ) -> FamilyProfile:
        if profile_id is None:
            return await self.get_self_profile(owner_user_id)
        else:
            return await self.get_by_id(profile_id, owner_user_id)
