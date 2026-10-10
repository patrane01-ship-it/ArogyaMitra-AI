from fastapi import APIRouter, Depends, Request, Response
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from backend.core.dependencies import get_current_user, get_health_api_service, require_tier
from backend.services.health_api_service import HealthAPIService
from backend.core.api_key_auth import get_api_key_credential
from backend.exceptions.arogya_errors import APIRateLimitError

# Router A: API Key Management
router_a = APIRouter(prefix="/api/api-keys", tags=["API Key Management"])

class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)

@router_a.post("/", dependencies=[Depends(require_tier("PRO"))])
async def create_api_key(
    req: CreateAPIKeyRequest,
    user_id: str = Depends(get_current_user),
    health_service: HealthAPIService = Depends(get_health_api_service)
):
    plain_key, api_key = await health_service.create_api_key(user_id, req.name)
    return {
        "message": "API Key created successfully. Save this key now, it will never be shown again.",
        "plain_key": plain_key,
        "api_key": api_key.to_dict()
    }

@router_a.get("/")
async def list_api_keys(
    user_id: str = Depends(get_current_user),
    health_service: HealthAPIService = Depends(get_health_api_service)
):
    keys = await health_service.list_api_keys(user_id)
    return {"api_keys": keys}

@router_a.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user),
    health_service: HealthAPIService = Depends(get_health_api_service)
):
    await health_service.revoke_api_key(key_id, user_id)
    return {"message": "API Key revoked successfully"}


# Router B: Health Score API v1
router_b = APIRouter(prefix="/v1", tags=["Health Score API v1"])

@router_b.get("/health-score/{profile_id}")
async def get_health_score(
    profile_id: str,
    response: Response,
    plain_key: str = Depends(get_api_key_credential),
    health_service: HealthAPIService = Depends(get_health_api_service)
):
    api_key = None
    status_code = 200
    try:
        api_key = await health_service.authenticate_api_key(plain_key)
        score_data = await health_service.get_health_score(api_key, profile_id)
        return score_data
    except APIRateLimitError as e:
        response.headers["Retry-After"] = "3600"
        status_code = 429
        raise e
    except Exception as e:
        status_code = getattr(e, "status_code", 500)
        raise e
    finally:
        if api_key:
            await health_service.api_key_repo.log_audit(
                api_key.key_id, 
                "/v1/health-score", 
                status_code, 
                profile_id
            )
