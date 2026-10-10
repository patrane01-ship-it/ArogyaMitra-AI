from fastapi import APIRouter, Depends
from typing import List, Optional
from pydantic import BaseModel
from backend.models.family_profile import FamilyProfile
from backend.services.doctor_workspace_service import DoctorWorkspaceService

# We will import get_doctor_workspace_service after defining it in dependencies.
from backend.core.dependencies import get_current_user, get_current_profile, require_tier, get_doctor_workspace_service

router = APIRouter(prefix="/api/doctor-access", tags=["Doctor Workspace"])
public_router = APIRouter(tags=["Doctor Workspace (Public)"])

class GrantAccessRequest(BaseModel):
    doctor_name: str
    doctor_email: str
    scope: List[str]
    expires_days: int = 30
    doctor_registration_number: Optional[str] = None
    specialization: Optional[str] = None

@router.post("/", dependencies=[Depends(require_tier("PREMIUM"))])
async def grant_access(
    req: GrantAccessRequest,
    user_id: str = Depends(get_current_user),
    profile: FamilyProfile = Depends(get_current_profile),
    workspace_service: DoctorWorkspaceService = Depends(get_doctor_workspace_service)
):
    access = await workspace_service.grant_access(
        granted_by_user_id=user_id,
        profile_id=profile.profile_id,
        doctor_name=req.doctor_name,
        doctor_email=req.doctor_email,
        scope=req.scope,
        expires_days=req.expires_days,
        doctor_registration_number=req.doctor_registration_number,
        specialization=req.specialization
    )
    return {"message": "Access granted", "access": access.to_dict()}

@router.get("/")
async def list_accesses(
    user_id: str = Depends(get_current_user),
    profile: FamilyProfile = Depends(get_current_profile),
    workspace_service: DoctorWorkspaceService = Depends(get_doctor_workspace_service)
):
    accesses = await workspace_service.list_accesses(profile.profile_id, user_id)
    return {"accesses": [a.to_dict() for a in accesses]}

@router.delete("/{access_id}")
async def revoke_access(
    access_id: str,
    user_id: str = Depends(get_current_user),
    workspace_service: DoctorWorkspaceService = Depends(get_doctor_workspace_service)
):
    await workspace_service.revoke_access(access_id, user_id)
    return {"message": "Access revoked"}

@public_router.get("/doctor-view/{token}")
async def doctor_view(
    token: str,
    workspace_service: DoctorWorkspaceService = Depends(get_doctor_workspace_service)
):
    data = await workspace_service.get_workspace_data(token)
    return data
