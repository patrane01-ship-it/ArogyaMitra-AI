from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime, timezone
import json

from backend.models.api_key import APIKey
from backend.repositories.api_key_repo import APIKeyRepository
from backend.repositories.risk_score_repo import RiskScoreRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.repositories.subscription_repo import SubscriptionRepository
from backend.repositories.family_profile_repo import FamilyProfileRepository
from backend.core.cache import ArogyaCache
from backend.config import Settings
from backend.exceptions.arogya_errors import FeatureNotAvailableError, APIRateLimitError, ConsentNotGrantedError, RecordNotFoundError
from backend.core.logger import logger


class HealthAPIService:
    def __init__(
        self,
        api_key_repo: APIKeyRepository,
        risk_repo: RiskScoreRepository,
        param_repo: ClinicalParameterRepository,
        subscription_repo: SubscriptionRepository,
        family_repo: FamilyProfileRepository,
        cache: ArogyaCache,
        settings: Settings,
    ):
        self.api_key_repo = api_key_repo
        self.risk_repo = risk_repo
        self.param_repo = param_repo
        self.subscription_repo = subscription_repo
        self.family_repo = family_repo
        self.cache = cache
        self.settings = settings

    async def create_api_key(self, user_id: str, name: str) -> Tuple[str, APIKey]:
        # Check PRO sub
        sub = await self.subscription_repo.get_active_subscription(user_id)
        if not sub or sub.tier != "PRO":
            raise FeatureNotAvailableError("API Key creation requires PRO subscription")

        plain_key, key_hash = APIKey.generate_key_pair()
        api_key = APIKey(user_id=user_id, name=name, api_key_hash=key_hash)
        api_key = await self.api_key_repo.create(api_key)
        
        return plain_key, api_key

    async def authenticate_api_key(self, plain_key: str) -> APIKey:
        api_key = await self.api_key_repo.get_by_hash(plain_key)
        
        # Check Redis rate limit
        rate_key = f"api_rate:{api_key.key_id}"
        
        if self.cache._redis_available:
            # Using raw redis for incr and expire
            current_count = await self.cache.redis.get(rate_key)
            if current_count and int(current_count) >= api_key.rate_limit:
                raise APIRateLimitError("API rate limit exceeded")
            
            pipe = self.cache.redis.pipeline()
            pipe.incr(rate_key)
            if not current_count:
                pipe.expire(rate_key, 3600)  # 1 hour
            await pipe.execute()

        await self.api_key_repo.update_last_used(api_key.key_id)
        return api_key

    async def get_health_score(self, api_key: APIKey, profile_id: str, scope: Optional[str] = None) -> Dict[str, Any]:
        # verify profile_id belongs to api_key.user_id (consent check via family profile lookup)
        profile = await self.family_repo.get_by_id(profile_id, api_key.user_id)
        if not profile:
            raise ConsentNotGrantedError("Patient has not granted consent for this API key to access their data")

        # fetch latest risk score
        latest_risk = await self.risk_repo.get_latest(api_key.user_id)
        
        # fetch params (last 30 days)
        # Using get_latest_for_user for simplicity, in a real scenario we could filter by date
        params = await self.param_repo.get_latest_for_user(api_key.user_id)

        return {
            "api_version": "v1",
            "profile_id": profile_id,
            "computed_at": latest_risk.computed_at.isoformat() if latest_risk else None,
            "overall_risk": latest_risk.overall_score if latest_risk else None,
            "risk_level": latest_risk.risk_level if latest_risk else None,
            "parameters": [
                {"name": p.param_name, "value": p.value, "unit": p.unit, "date": p.report_date.isoformat()}
                for p in params
            ]
        }

    async def list_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        keys = await self.api_key_repo.list_for_user(user_id)
        # to_dict() does not include api_key_hash
        return [k.to_dict() for k in keys]

    async def revoke_api_key(self, key_id: str, user_id: str) -> None:
        await self.api_key_repo.revoke(key_id, user_id)
        # delete rate limit cache
        rate_key = f"api_rate:{key_id}"
        if self.cache._redis_available:
            await self.cache.redis.delete(rate_key)
