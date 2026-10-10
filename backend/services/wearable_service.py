"""
ArogyaMitra AI - Wearable Service (Phase 3)
Business logic for wearable integrations.
"""

from typing import List, Dict, Any, Optional
import uuid
import datetime
from backend.repositories.wearable_repo import WearableRepository
from backend.services.encryption_service import EncryptionService
from backend.core.cache import ArogyaCache
from backend.config import Settings
from backend.adapters.wearable_adapter import WearableAdapterFactory
from backend.exceptions.arogya_errors import WearableAuthError, WearableSyncError
from backend.models.wearable_reading import WearableReading

class WearableService:
    def __init__(self, repo: WearableRepository, encryption_service: EncryptionService, cache: ArogyaCache, settings: Settings):
        self.repo = repo
        self.encryption_service = encryption_service
        self.cache = cache
        self.settings = settings
        self.redirect_uri = f"http://localhost:8000/api/wearables/callback"

    async def get_auth_url(self, profile_id: str, source: str) -> str:
        adapter = WearableAdapterFactory.get(source, self.settings)
        state = f"{profile_id}::{source}::{str(uuid.uuid4())}"
        
        # Store state to validate on callback
        await self.cache.set(f"oauth_state:{state}", "1", ttl=600)
        
        auth_info = await adapter.get_auth_url(state, self.redirect_uri)
        return auth_info.url

    async def handle_oauth_callback(self, profile_id: str, source: str, code: str, state: str) -> None:
        # Validate state
        valid = await self.cache.get(f"oauth_state:{state}")
        if not valid:
            raise WearableAuthError("Invalid or expired OAuth state")
        await self.cache.delete(f"oauth_state:{state}")
        
        adapter = WearableAdapterFactory.get(source, self.settings)
        token_info = await adapter.exchange_code(code, self.redirect_uri)
        
        access_encrypted = self.encryption_service.encrypt(token_info.access_token)
        refresh_encrypted = self.encryption_service.encrypt(token_info.refresh_token)
        
        await self.repo.store_wearable_token(profile_id, source, access_encrypted, refresh_encrypted)

    async def sync_readings(self, profile_id: str, source: str) -> Dict[str, Any]:
        access_encrypted = await self.repo.get_wearable_token(profile_id, source)
        if not access_encrypted:
            raise WearableAuthError(f"No active connection for {source}")
            
        access_token = self.encryption_service.decrypt(access_encrypted)
        adapter = WearableAdapterFactory.get(source, self.settings)
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        try:
            raw_readings = await adapter.fetch_readings(access_token, date_str)
        except WearableAuthError:
            # Need to refresh token (for simplicity here, we'll mark reconnect)
            await self.repo.mark_needs_reconnect(profile_id, source)
            raise WearableAuthError(f"Token expired for {source}. Reconnection required.")
            
        readings = []
        for rr in raw_readings:
            # Anomaly logic: hr < 30 or hr > 250
            is_anomaly = False
            if rr.metric_type == "HEART_RATE" and (rr.value < 30 or rr.value > 250):
                is_anomaly = True
                
            readings.append(WearableReading(
                profile_id=profile_id,
                source=rr.source,
                metric_type=rr.metric_type,
                value=rr.value,
                unit=rr.unit,
                recorded_at=rr.recorded_at,
                raw_payload=rr.raw_payload,
                is_anomaly=is_anomaly
            ))
            
        count = await self.repo.bulk_upsert(readings)
        return {"inserted_count": count}

    async def list_readings(self, profile_id: str, metric_type: Optional[str] = None) -> List[WearableReading]:
        return await self.repo.list_for_profile(profile_id, metric_type)

    async def disconnect(self, profile_id: str, source: str) -> None:
        await self.cache.delete(f"wearable_token:{profile_id}:{source}")
        await self.cache.delete(f"wearable_refresh:{profile_id}:{source}")
