"""
ArogyaMitra AI - Family Profiles Router (Phase 3)
Endpoints for family member management.
Per FEATURES_PHASE3.md §2.1 and §3 F1.
"""
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from backend.core.dependencies import get_current_user, get_family_service
from backend.services.family_service import FamilyService

router = APIRouter(prefix='/api/family', tags=['Family Profiles'])


class AddMemberRequest(BaseModel):
    member_name: str
    relation: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    abha_id: Optional[str] = None


class UpdateMemberRequest(BaseModel):
    member_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    abha_id: Optional[str] = None


@router.post('/', status_code=status.HTTP_201_CREATED)
async def add_member(
    body: AddMemberRequest,
    user_id: str = Depends(get_current_user),
    service: FamilyService = Depends(get_family_service),
):
    """Add a new family member profile."""
    profile = await service.add_member(
        owner_user_id=user_id,
        member_name=body.member_name,
        relation=body.relation,
        date_of_birth=body.date_of_birth,
        gender=body.gender,
        abha_id=body.abha_id,
    )
    return {"profile": profile.to_dict()}


@router.get('/', status_code=status.HTTP_200_OK)
async def list_members(
    user_id: str = Depends(get_current_user),
    service: FamilyService = Depends(get_family_service),
):
    """List all active family member profiles."""
    members = await service.list_members(user_id)
    return {"members": [m.to_dict() for m in members]}


@router.get('/{profile_id}', status_code=status.HTTP_200_OK)
async def get_member(
    profile_id: str,
    user_id: str = Depends(get_current_user),
    service: FamilyService = Depends(get_family_service),
):
    """Get a single family member profile."""
    profile = await service.get_member(profile_id, user_id)
    return {"profile": profile.to_dict()}


@router.put('/{profile_id}', status_code=status.HTTP_200_OK)
async def update_member(
    profile_id: str,
    body: UpdateMemberRequest,
    user_id: str = Depends(get_current_user),
    service: FamilyService = Depends(get_family_service),
):
    """Update family member details."""
    profile = await service.update_member(
        profile_id=profile_id,
        owner_user_id=user_id,
        member_name=body.member_name,
        date_of_birth=body.date_of_birth,
        gender=body.gender,
        abha_id=body.abha_id,
    )
    return {"profile": profile.to_dict()}


@router.delete('/{profile_id}', status_code=status.HTTP_200_OK)
async def deactivate_member(
    profile_id: str,
    user_id: str = Depends(get_current_user),
    service: FamilyService = Depends(get_family_service),
):
    """Soft-deactivate a family member. Cannot deactivate SELF profile."""
    await service.deactivate_member(profile_id, user_id)
    return {"message": "Family member deactivated"}


@router.post('/{profile_id}/activate', status_code=status.HTTP_200_OK)
async def activate_member(
    profile_id: str,
    user_id: str = Depends(get_current_user),
    service: FamilyService = Depends(get_family_service),
):
    """Set active context to this family member (returns the profile)."""
    profile = await service.get_member(profile_id, user_id)
    return {"active_profile": profile.to_dict(), "message": f"Active profile set to {profile.member_name}"}
