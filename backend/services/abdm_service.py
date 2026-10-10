import base64
import json
from typing import Dict, Any
from backend.core.cache import ArogyaCache
import backend.core.cache as cache_module
from backend.services.encryption_service import EncryptionService
from backend.repositories.health_record_repo import HealthRecordRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.adapters.abdm_adapter import ABDMAdapter
from backend.core.logger import logger
from backend.exceptions.arogya_errors import ArogyaError
from backend.models.health_record import HealthRecord

class ABDMSyncCooldownError(ArogyaError):
    def __init__(self):
        super().__init__("ABDM sync is on cooldown. Please try again later.", status_code=429)

class FHIRParseError(ArogyaError):
    def __init__(self, msg: str):
        super().__init__(msg, status_code=400)

class ABDMService:
    def __init__(self, adapter: ABDMAdapter, encryption_service: EncryptionService, record_repo: HealthRecordRepository, param_repo: ClinicalParameterRepository, cache: ArogyaCache):
        self.adapter = adapter
        self.encryption_service = encryption_service
        self.record_repo = record_repo
        self.param_repo = param_repo
        self.cache = cache
        
        # Patch TTLs
        cache_module.CACHE_TTL_SECONDS["abdm_token"] = 3600
        cache_module.CACHE_TTL_SECONDS["abdm_sync"] = 86400
        
    async def link_abha(self, profile_id: str, abha_id: str, otp: str) -> str:
        # Authenticate
        token = await self.adapter.authenticate(abha_id, otp)
        
        # Encrypt token
        encrypted_bytes = self.encryption_service.encrypt_to_payload(token.encode())
        encrypted_token_str = base64.b64encode(encrypted_bytes).decode('utf-8')
        
        await self.cache.set("abdm_token", profile_id, encrypted_token_str)
        return "ABHA linked successfully"

    async def sync_records(self, profile_id: str, owner_user_id: str) -> Dict[str, Any]:
        cooldown = await self.cache.get("abdm_sync", profile_id)
        if cooldown:
            raise ABDMSyncCooldownError()
            
        encrypted_token_str = await self.cache.get("abdm_token", profile_id)
        if not encrypted_token_str:
            raise ArogyaError("ABDM access token not found or expired. Please link ABHA again.", status_code=401)
            
        encrypted_bytes = base64.b64decode(encrypted_token_str)
        token = self.encryption_service.decrypt_from_payload(encrypted_bytes).decode('utf-8')
        
        fhir_records = await self.adapter.fetch_records(token)
        
        synced = 0
        skipped = 0
        errors = 0
        
        existing_records = await self.record_repo.list_for_profile(profile_id, owner_user_id)
        existing_titles = {r.record_title for r in existing_records}
        
        for record in fhir_records:
            try:
                parsed_data = self.parse_fhir_record(record.data)
                record_title = f"ABDM {record.resource_type} {record.resource_id}"
                
                if record_title in existing_titles:
                    skipped += 1
                    continue
                    
                new_record = HealthRecord(
                    profile_id=profile_id,
                    owner_user_id=owner_user_id,
                    record_title=record_title,
                    record_type="observation",
                    file_url=None,
                    summary=json.dumps(parsed_data)
                )
                await self.record_repo.create(new_record)
                synced += 1
                
            except FHIRParseError as e:
                logger.warning(f"Failed to parse FHIR record {record.resource_id}: {e}")
                errors += 1
                
        await self.cache.set("abdm_sync", profile_id, True)
        
        return {
            "synced": synced,
            "skipped": skipped,
            "errors": errors
        }

    def parse_fhir_record(self, record_data: dict) -> dict:
        if record_data.get("resourceType") != "Observation":
            raise FHIRParseError("Unsupported resourceType")
        
        try:
            return {
                "id": record_data["id"],
                "status": record_data["status"],
                "code": record_data["code"]["coding"][0]["code"],
                "display": record_data["code"]["coding"][0]["display"],
                "value": record_data["valueQuantity"]["value"],
                "unit": record_data["valueQuantity"]["unit"],
                "effective_date": record_data.get("effectiveDateTime")
            }
        except KeyError as e:
            raise FHIRParseError(f"Missing expected FHIR field: {e}")
