"""
ArogyaMitra AI - Wearable Router (Phase 3)
API endpoints for wearable integration.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from backend.core.dependencies import (
    get_wearable_service,
    get_current_user,
    get_current_profile,
    require_tier,
    get_wearable_repo
)
from backend.services.wearable_service import WearableService
from backend.models.family_profile import FamilyProfile
from backend.repositories.wearable_repo import WearableRepository

router = APIRouter(prefix="/api/wearables", tags=["Wearables"])

class SyncRequest(BaseModel):
    source: str

@router.post("/connect/{source}")
async def connect_wearable(
    source: str,
    tier: str = Depends(require_tier("PREMIUM")),
    profile: FamilyProfile = Depends(get_current_profile),
    wearable_service: WearableService = Depends(get_wearable_service)
):
    """Initiate OAuth flow for a wearable device."""
    url = await wearable_service.get_auth_url(profile.profile_id, source.upper())
    return {"auth_url": url}

@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    wearable_service: WearableService = Depends(get_wearable_service)
):
    """OAuth callback endpoint."""
    try:
        # state format: profile_id::source::uuid
        parts = state.split("::")
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        profile_id, source, _ = parts
        await wearable_service.handle_oauth_callback(profile_id, source, code, state)
        return {"message": f"Successfully connected to {source}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sync")
async def sync_wearable(
    request: SyncRequest,
    tier: str = Depends(require_tier("PREMIUM")),
    profile: FamilyProfile = Depends(get_current_profile),
    wearable_service: WearableService = Depends(get_wearable_service)
):
    """Manual sync for a wearable device."""
    result = await wearable_service.sync_readings(profile.profile_id, request.source.upper())
    return result

@router.get("/")
async def list_wearable_readings(
    metric_type: Optional[str] = Query(None),
    tier: str = Depends(require_tier("PREMIUM")),
    profile: FamilyProfile = Depends(get_current_profile),
    wearable_service: WearableService = Depends(get_wearable_service)
):
    """List wearable readings for the current profile."""
    readings = await wearable_service.list_readings(profile.profile_id, metric_type)
    return [r.to_dict() for r in readings]

@router.delete("/{reading_id}")
async def delete_reading(
    reading_id: str,
    user_id: str = Depends(get_current_user),
    profile: FamilyProfile = Depends(get_current_profile),
    repo: WearableRepository = Depends(get_wearable_repo)
):
    """Delete a specific wearable reading."""
    await repo.delete(reading_id, profile.profile_id)
    return {"message": "Reading deleted"}

@router.delete("/connect/{source}")
async def disconnect_wearable(
    source: str,
    user_id: str = Depends(get_current_user),
    profile: FamilyProfile = Depends(get_current_profile),
    wearable_service: WearableService = Depends(get_wearable_service)
):
    """Disconnect a wearable device."""
    await wearable_service.disconnect(profile.profile_id, source.upper())
    return {"message": f"Disconnected from {source}"}
