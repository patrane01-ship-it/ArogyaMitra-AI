from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from backend.models.doctor_access import DoctorAccess
from backend.repositories.doctor_access_repo import DoctorAccessRepository
from backend.repositories.health_record_repo import HealthRecordRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.repositories.risk_score_repo import RiskScoreRepository
from backend.repositories.subscription_repo import SubscriptionRepository
from backend.exceptions.arogya_errors import ArogyaError, FeatureNotAvailableError
from backend.config import Settings
import uuid

class DoctorWorkspaceService:
    def __init__(self, 
                 access_repo: DoctorAccessRepository, 
                 record_repo: HealthRecordRepository, 
                 param_repo: ClinicalParameterRepository, 
                 risk_repo: RiskScoreRepository, 
                 subscription_repo: SubscriptionRepository, 
                 settings: Settings):
        self.access_repo = access_repo
        self.record_repo = record_repo
        self.param_repo = param_repo
        self.risk_repo = risk_repo
        self.subscription_repo = subscription_repo
        self.settings = settings

    async def grant_access(self, granted_by_user_id: str, profile_id: str, doctor_name: str, doctor_email: str, scope: List[str], expires_days: int = 30, doctor_registration_number: Optional[str] = None, specialization: Optional[str] = None) -> DoctorAccess:
        # Check doctor limit vs subscription
        sub = await self.subscription_repo.get_active_subscription(granted_by_user_id)
        tier = sub.tier if sub else "FREE"
        
        limit_map = {"FREE": 1, "PREMIUM": 5, "PRO": 9999}
        limit = limit_map.get(tier, 1)
        
        active_count = await self.access_repo.count_active_for_user(granted_by_user_id)
        if active_count >= limit:
            raise ArogyaError(f"Workspace limit reached for {tier} tier. Upgrade to grant more.", status_code=403)
            
        access = DoctorAccess(
            patient_profile_id=profile_id,
            granted_by_user_id=granted_by_user_id,
            doctor_name=doctor_name,
            doctor_email=doctor_email,
            doctor_registration_number=doctor_registration_number,
            specialization=specialization,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days)
        )
        access.set_scope(scope)
        return await self.access_repo.create(access)

    async def get_workspace_data(self, token: str) -> Dict[str, Any]:
        access = await self.access_repo.get_by_token(token)
        await self.access_repo.record_access(access)
        
        scope = access.get_scope()
        data = {
            "doctor_info": {
                "name": access.doctor_name,
                "email": access.doctor_email
            },
            "patient_profile_id": access.patient_profile_id,
            "expires_at": access.expires_at.isoformat(),
        }
        
        if "records" in scope:
            records = await self.record_repo.list_for_profile(access.patient_profile_id, access.granted_by_user_id)
            data["records"] = [{"id": r.record_id, "title": r.record_title, "type": r.record_type, "date": r.record_date.isoformat() if r.record_date else None, "summary": r.summary} for r in records]
            
        if "timeline" in scope:
            params = await self.param_repo.list_for_profile(access.patient_profile_id, access.granted_by_user_id)
            data["timeline"] = [{"name": p.parameter_name, "value": p.value, "unit": p.unit, "date": p.recorded_at.isoformat() if p.recorded_at else None} for p in params]
            
        if "risk" in scope:
            risk = await self.risk_repo.get_latest_for_profile(access.patient_profile_id, access.granted_by_user_id)
            data["risk"] = risk.to_dict() if risk else None
            
        return data

    async def revoke_access(self, access_id: str, owner_user_id: str) -> None:
        await self.access_repo.revoke(access_id, owner_user_id)

    async def list_accesses(self, profile_id: str, owner_user_id: str) -> List[DoctorAccess]:
        return await self.access_repo.list_for_profile(profile_id, owner_user_id)
