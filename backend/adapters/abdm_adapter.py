from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class FHIRRecord:
    resource_id: str
    resource_type: str
    record_date: datetime
    data: Dict[str, Any]

class ABDMAdapter(ABC):
    """Abstract Base Class for ABDM integration."""
    
    @abstractmethod
    async def authenticate(self, abha_id: str, otp: str) -> str:
        """Authenticate with ABHA ID and OTP to get access token."""
        pass

    @abstractmethod
    async def fetch_records(self, access_token: str) -> List[FHIRRecord]:
        """Fetch FHIR records for the authenticated user."""
        pass

class MockABDMAdapter(ABDMAdapter):
    """Mock implementation for local development."""
    
    async def authenticate(self, abha_id: str, otp: str) -> str:
        if otp != "123456":
            raise ValueError("Invalid OTP. Use 123456 for testing.")
        return f"mock_abdm_token_for_{abha_id}"

    async def fetch_records(self, access_token: str) -> List[FHIRRecord]:
        return [
            FHIRRecord(
                resource_id="obs-001",
                resource_type="Observation",
                record_date=datetime.now(timezone.utc),
                data={
                    "resourceType": "Observation",
                    "id": "obs-001",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "2339-0", "display": "Glucose [Mass/volume] in Blood"}]
                    },
                    "valueQuantity": {"value": 110, "unit": "mg/dL", "system": "http://unitsofmeasure.org", "code": "mg/dL"},
                    "effectiveDateTime": datetime.now(timezone.utc).isoformat()
                }
            )
        ]
