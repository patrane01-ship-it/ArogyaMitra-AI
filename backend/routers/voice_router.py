"""
ArogyaMitra AI - Voice Router (Phase 3)
Per FEATURES_PHASE3.md §2.7
"""

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.core.dependencies import get_voice_service, get_current_user, get_current_profile, get_cache
from backend.core.cache import ArogyaCache
from backend.services.voice_service import VoiceService
from backend.models.family_profile import FamilyProfile
from backend.exceptions.arogya_errors import APIRateLimitError

router = APIRouter(prefix="/api/voice", tags=["Voice Input"])


class ConfirmVoiceRequest(BaseModel):
    session_id: str
    confirmed_data: Optional[Dict[str, Any]] = None

class DiscardVoiceRequest(BaseModel):
    session_id: str
    profile_id: Optional[str] = None


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    profile: FamilyProfile = Depends(get_current_profile),
    cache: ArogyaCache = Depends(get_cache),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """Upload audio, get transcript (not saved yet)."""
    # Rate limit by user_id
    rate_key = f"voice_rate:{profile.user_id}"
    requests = await cache.increment(rate_key)
    if requests == 1:
        await cache.expire(rate_key, 3600)
    if requests > 10:
        raise APIRateLimitError("Too many voice requests. Please wait before trying again.")

    result = await voice_service.transcribe(file, profile.profile_id)
    return result


@router.post("/confirm")
async def confirm_voice(
    req: ConfirmVoiceRequest,
    profile: FamilyProfile = Depends(get_current_profile),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """Confirm and save health data from voice session."""
    result = await voice_service.confirm_and_save(profile.profile_id, req.session_id, req.confirmed_data)
    return result


@router.post("/discard")
async def discard_voice(
    req: DiscardVoiceRequest,
    user_id: str = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """Discard a voice session."""
    p_id = req.profile_id or user_id
    await voice_service.discard(p_id, req.session_id)
    return {"message": "Session discarded"}
