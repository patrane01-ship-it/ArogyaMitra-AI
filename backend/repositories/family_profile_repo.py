"""
ArogyaMitra AI - FamilyProfile Repository (Phase 3)
Data access layer for FamilyProfile entity.
Per FEATURES_PHASE3.md §2.1.
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.models.family_profile import FamilyProfile
from backend.core.logger import logger
from backend.exceptions.arogya_errors import (
    DatabaseError,
    FamilyProfileNotFoundError,
    CannotDeletePrimaryProfileError,
    FamilyMemberLimitError,
)


class FamilyProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, profile: FamilyProfile, max_members: int = 10) -> FamilyProfile:
        """Create a new family profile, enforcing member limit."""
        current_count = await self.count_active_members(profile.owner_user_id)
        if current_count >= max_members:
            raise FamilyMemberLimitError(
                f"Maximum {max_members} family members allowed on your plan"
            )
        try:
            profile.validate()
            self.db.add(profile)
            await self.db.flush()
            return profile
        except (FamilyMemberLimitError, CannotDeletePrimaryProfileError):
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:FamilyProfile] Error creating profile: {e}")
            raise DatabaseError("Failed to create family profile")

    async def get_by_id(self, profile_id: str, owner_user_id: str) -> Optional[FamilyProfile]:
        """Get profile by ID scoped to the owning user."""
        try:
            stmt = select(FamilyProfile).where(
                FamilyProfile.profile_id == profile_id,
                FamilyProfile.owner_user_id == owner_user_id,
                FamilyProfile.is_active.is_(True),
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:FamilyProfile] get_by_id error: {e}")
            raise DatabaseError("Database error during profile lookup")

    async def get_all_for_user(self, owner_user_id: str) -> List[FamilyProfile]:
        """Get all active profiles for a user."""
        try:
            stmt = select(FamilyProfile).where(
                FamilyProfile.owner_user_id == owner_user_id,
                FamilyProfile.is_active.is_(True),
            ).order_by(FamilyProfile.is_primary.desc(), FamilyProfile.created_at.asc())
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"[Repo:FamilyProfile] get_all_for_user error: {e}")
            raise DatabaseError("Failed to fetch family profiles")

    async def get_primary(self, owner_user_id: str) -> Optional[FamilyProfile]:
        """Get the primary (SELF) profile for a user."""
        try:
            stmt = select(FamilyProfile).where(
                FamilyProfile.owner_user_id == owner_user_id,
                FamilyProfile.is_primary.is_(True),
                FamilyProfile.is_active.is_(True),
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:FamilyProfile] get_primary error: {e}")
            raise DatabaseError("Failed to fetch primary profile")

    async def update(
        self,
        profile_id: str,
        owner_user_id: str,
        member_name: str = None,
        date_of_birth=None,
        gender: str = None,
        abha_id: str = None,
    ) -> Optional[FamilyProfile]:
        """Update editable fields of a family profile."""
        profile = await self.get_by_id(profile_id, owner_user_id)
        if not profile:
            return None
        if member_name is not None:
            profile.member_name = member_name
        if date_of_birth is not None:
            profile.date_of_birth = date_of_birth
        if gender is not None:
            profile.gender = gender
        if abha_id is not None:
            profile.abha_id = abha_id
        try:
            profile.validate()
            await self.db.flush()
            return profile
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:FamilyProfile] update error: {e}")
            raise DatabaseError("Failed to update family profile")

    async def deactivate(self, profile_id: str, owner_user_id: str) -> bool:
        """Soft-delete a family profile. Cannot deactivate primary SELF profile."""
        profile = await self.get_by_id(profile_id, owner_user_id)
        if not profile:
            return False
        if profile.is_primary:
            raise CannotDeletePrimaryProfileError()
        profile.is_active = False
        await self.db.flush()
        return True

    async def count_active_members(self, owner_user_id: str) -> int:
        """Count active family profiles for a user."""
        try:
            from sqlalchemy import func
            stmt = select(func.count()).select_from(FamilyProfile).where(
                FamilyProfile.owner_user_id == owner_user_id,
                FamilyProfile.is_active.is_(True),
            )
            result = await self.db.execute(stmt)
            return result.scalar_one() or 0
        except Exception as e:
            logger.error(f"[Repo:FamilyProfile] count error: {e}")
            return 0
