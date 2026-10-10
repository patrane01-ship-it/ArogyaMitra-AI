"""
ArogyaMitra AI - Wearable Adapters (Phase 3)
Provides integration with wearable APIs. Fitbit is implemented, others deferred.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import httpx
import base64
from datetime import datetime, timezone
import uuid

from backend.config import Settings
from backend.exceptions.arogya_errors import WearableAuthError, WearableSyncError

@dataclass
class WearableAuthURL:
    url: str
    state: str

@dataclass
class WearableToken:
    access_token: str
    refresh_token: str
    expires_in: int

@dataclass
class RawReading:
    source: str
    metric_type: str
    value: float
    unit: str
    recorded_at: datetime
    raw_payload: str

class WearableAdapter(ABC):
    @abstractmethod
    async def get_auth_url(self, state: str, redirect_uri: str) -> WearableAuthURL:
        pass

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> WearableToken:
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> WearableToken:
        pass

    @abstractmethod
    async def fetch_readings(self, access_token: str, date: str) -> List[RawReading]:
        pass

class FitbitAdapter(WearableAdapter):
    def __init__(self, settings: Settings):
        self.client_id = getattr(settings, 'FITBIT_CLIENT_ID', 'dummy_client_id')
        self.client_secret = getattr(settings, 'FITBIT_CLIENT_SECRET', 'dummy_client_secret')
        self.auth_base_url = "https://www.fitbit.com/oauth2/authorize"
        self.token_url = "https://api.fitbit.com/oauth2/token"
        self.api_base_url = "https://api.fitbit.com/1"

    async def get_auth_url(self, state: str, redirect_uri: str) -> WearableAuthURL:
        scope = "heartrate sleep activity profile"
        url = f"{self.auth_base_url}?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}"
        return WearableAuthURL(url=url, state=state)

    async def exchange_code(self, code: str, redirect_uri: str) -> WearableToken:
        auth_str = f"{self.client_id}:{self.client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.token_url, headers=headers, data=data)
            if resp.status_code != 200:
                raise WearableAuthError(f"Failed to exchange code: {resp.text}")
            resp_data = resp.json()
            return WearableToken(
                access_token=resp_data["access_token"],
                refresh_token=resp_data["refresh_token"],
                expires_in=resp_data["expires_in"]
            )

    async def refresh_token(self, refresh_token: str) -> WearableToken:
        auth_str = f"{self.client_id}:{self.client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.token_url, headers=headers, data=data)
            if resp.status_code != 200:
                raise WearableAuthError(f"Failed to refresh token: {resp.text}")
            resp_data = resp.json()
            return WearableToken(
                access_token=resp_data["access_token"],
                refresh_token=resp_data["refresh_token"],
                expires_in=resp_data["expires_in"]
            )

    async def fetch_readings(self, access_token: str, date: str) -> List[RawReading]:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.api_base_url}/user/-/activities/heart/date/{date}/1d.json"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 401:
                raise WearableAuthError("Access token expired")
            elif resp.status_code != 200:
                raise WearableSyncError(f"Failed to fetch Fitbit data: {resp.text}")
                
            data = resp.json()
            readings = []
            hr_series = data.get("activities-heart-intraday", {}).get("dataset", [])
            for item in hr_series:
                time_str = item["time"]
                try:
                    dt = datetime.fromisoformat(f"{date}T{time_str}").replace(tzinfo=timezone.utc)
                except ValueError:
                    dt = datetime.now(timezone.utc)
                    
                readings.append(RawReading(
                    source="FITBIT",
                    metric_type="HEART_RATE",
                    value=float(item["value"]),
                    unit="bpm",
                    recorded_at=dt,
                    raw_payload=str(item)
                ))
            return readings

class DeferredWearableAdapter(WearableAdapter):
    def __init__(self, source: str):
        self.source = source

    async def get_auth_url(self, state: str, redirect_uri: str) -> WearableAuthURL:
        raise WearableAuthError(f"Integration with {self.source} is coming soon.")

    async def exchange_code(self, code: str, redirect_uri: str) -> WearableToken:
        raise WearableAuthError(f"Integration with {self.source} is coming soon.")

    async def refresh_token(self, refresh_token: str) -> WearableToken:
        raise WearableAuthError(f"Integration with {self.source} is coming soon.")

    async def fetch_readings(self, access_token: str, date: str) -> List[RawReading]:
        raise WearableAuthError(f"Integration with {self.source} is coming soon.")

class WearableAdapterFactory:
    @staticmethod
    def get(source: str, settings: Settings) -> WearableAdapter:
        if source == "FITBIT":
            return FitbitAdapter(settings)
        elif source in ["MI_BAND", "GARMIN", "SAMSUNG_HEALTH"]:
            return DeferredWearableAdapter(source)
        else:
            raise ValueError(f"Unknown wearable source: {source}")
