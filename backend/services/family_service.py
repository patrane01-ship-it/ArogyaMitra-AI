"""
ArogyaMitra AI - Family Service (Phase 3)
Business logic for Family Profiles.
"""

from typing import Optional, Any
from backend.models.family_profile import FamilyProfile
from backend.repositories.family_profile_repo import FamilyProfileRepository
from backend.exceptions.arogya_errors import FamilyMemberLimitError

class FamilyService:
    def __init__(self, repo: FamilyProfileRepository, subscription_repo: Any):
        self.repo = repo
        self.subscription_repo = subscription_repo

    async def create_self_profile(self, owner_user_id: str, member_name: str) -> FamilyProfile:
        """Auto-called after registration. Creates is_primary=True SELF profile."""
        try:
            return await self.repo.get_self_profile(owner_user_id)
        except Exception:
            pass # Not found, proceed to create
            
        profile = FamilyProfile(
            owner_user_id=owner_user_id,
            member_name=member_name,
            relation='SELF',
            is_primary=True,
            is_active=True
        )
        return await self.repo.create(profile)

    async def add_member(
        self, owner_user_id: str, member_name: str, relation: str,
        date_of_birth=None, gender=None, abha_id=None
    ) -> FamilyProfile:
        """Add a new family member. Enforces tier limit."""
        limit = await self.subscription_repo.get_tier_limit(owner_user_id, "family_members")
        if limit is None:
            limit = 2
            
        count = await self.repo.count_active(owner_user_id)
        if count >= limit:
            raise FamilyMemberLimitError(f"Maximum {limit} family members allowed on your plan")
            
        profile = FamilyProfile(
            owner_user_id=owner_user_id,
            member_name=member_name,
            relation=relation,
            date_of_birth=date_of_birth,
            gender=gender,
            abha_id=abha_id,
            is_primary=False,
            is_active=True
        )
        return await self.repo.create(profile)

    async def list_members(self, owner_user_id: str) -> list[FamilyProfile]:
        return await self.repo.list_by_owner(owner_user_id)

    async def get_member(self, profile_id: str, owner_user_id: str) -> FamilyProfile:
        return await self.repo.get_by_id(profile_id, owner_user_id)

    async def update_member(
        self, profile_id: str, owner_user_id: str, **updates
    ) -> FamilyProfile:
        """Update member fields. Cannot change relation for SELF profile."""
        profile = await self.repo.get_by_id(profile_id, owner_user_id)
        if profile.is_primary and 'relation' in updates and updates['relation'] != 'SELF':
            raise ValueError('Cannot change relation of primary SELF profile')
            
        for k, v in updates.items():
            if v is not None and hasattr(profile, k):
                setattr(profile, k, v)
                
        return await self.repo.update(profile)

    async def deactivate_member(self, profile_id: str, owner_user_id: str) -> None:
        await self.repo.deactivate(profile_id, owner_user_id)

    async def get_profile_for_request(
        self, profile_id: Optional[str], owner_user_id: str
    ) -> FamilyProfile:
        return await self.repo.get_profile_for_request(profile_id, owner_user_id)
