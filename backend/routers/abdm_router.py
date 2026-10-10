from fastapi import APIRouter, Depends, Body
from typing import Dict, Any
from backend.core.dependencies import get_current_user, get_current_profile
from backend.models.family_profile import FamilyProfile
from backend.services.abdm_service import ABDMService
from pydantic import BaseModel

# We will need to import get_abdm_service from core.dependencies but we haven't added it yet. 
# We'll add it to dependencies and then use it here.
from backend.core.dependencies import get_abdm_service

router = APIRouter(prefix="/api/abdm", tags=["ABDM/FHIR"])

class LinkRequest(BaseModel):
    abha_id: str
    otp: str

@router.post("/link")
async def link_abha(
    req: LinkRequest,
    user_id: str = Depends(get_current_user),
    profile: FamilyProfile = Depends(get_current_profile),
    abdm_service: ABDMService = Depends(get_abdm_service)
):
    msg = await abdm_service.link_abha(profile.profile_id, req.abha_id, req.otp)
    return {"message": msg}

@router.post("/sync")
async def sync_records(
    user_id: str = Depends(get_current_user),
    profile: FamilyProfile = Depends(get_current_profile),
    abdm_service: ABDMService = Depends(get_abdm_service)
):
    result = await abdm_service.sync_records(profile.profile_id, user_id)
    return {"message": "Sync completed", "details": result}

@router.get("/status")
async def get_status(
    user_id: str = Depends(get_current_user),
    profile: FamilyProfile = Depends(get_current_profile),
    abdm_service: ABDMService = Depends(get_abdm_service)
):
    is_linked = bool(await abdm_service.cache.get("abdm_token", profile.profile_id))
    last_sync_cooldown = bool(await abdm_service.cache.get("abdm_sync", profile.profile_id))
    return {
        "is_linked": is_linked,
        "sync_in_cooldown": last_sync_cooldown
    }
