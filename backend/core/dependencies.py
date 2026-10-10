"""
ArogyaMitra AI - Dependency Injection Registry
Central repository for FastAPI dependencies.
Per PRODUCTION_BACKEND.md §5.1 and FEATURES_PHASE2.md §2.1.
"""

from fastapi import Depends, Request, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config import settings, Settings
from backend.database import get_db
from backend.core.cache import get_cache, ArogyaCache
from backend.models.family_profile import FamilyProfile
from backend.exceptions.arogya_errors import FeatureNotAvailableError
from backend.config import settings, Settings
from backend.database import get_db
from backend.core.cache import get_cache, ArogyaCache
from backend.services.ocr_service import OCRService
from backend.services.encryption_service import EncryptionService
from backend.services.auth_service import AuthService
from backend.repositories.health_record_repo import HealthRecordRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.repositories.risk_score_repo import RiskScoreRepository
from backend.repositories.reminder_repo import ReminderRepository
from backend.repositories.doctor_report_repo import DoctorReportRepository
from backend.repositories.user_repo import UserRepository
from backend.exceptions.arogya_errors import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
)


# Stateless singletons
_ocr_service_instance = OCRService()
_encryption_service_instance = None


def get_settings() -> Settings:
    """Settings dependency."""
    return settings


def get_ocr_service() -> OCRService:
    """OCR service dependency."""
    return _ocr_service_instance


def get_encryption_service() -> EncryptionService:
    """Encryption service dependency configured with application secret."""
    global _encryption_service_instance
    if _encryption_service_instance is None:
        _encryption_service_instance = EncryptionService(settings.ENCRYPTION_KEY.encode())
    return _encryption_service_instance


async def get_current_user(request: Request) -> str:
    """
    Phase 2 JWT Authentication dependency.
    Extracts and validates Bearer token from Authorization header.
    Returns the authenticated user_id string.
    Raises AuthenticationError / InvalidTokenError / TokenExpiredError on failure.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or malformed Authorization header. Expected: Bearer <token>")

    token = auth_header[7:].strip()
    if not token:
        raise AuthenticationError("Access token is empty")

    # Raises InvalidTokenError or TokenExpiredError on failure
    user_id = AuthService.extract_user_id(token)
    return user_id


def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """UserRepository dependency."""
    return UserRepository(db)


def get_record_repo(db: AsyncSession = Depends(get_db)) -> HealthRecordRepository:
    """HealthRecordRepository dependency."""
    return HealthRecordRepository(db)


def get_param_repo(db: AsyncSession = Depends(get_db)) -> ClinicalParameterRepository:
    """ClinicalParameterRepository dependency."""
    return ClinicalParameterRepository(db)


def get_risk_repo(db: AsyncSession = Depends(get_db)) -> RiskScoreRepository:
    """RiskScoreRepository dependency."""
    return RiskScoreRepository(db)


def get_reminder_repo(db: AsyncSession = Depends(get_db)) -> ReminderRepository:
    """ReminderRepository dependency."""
    return ReminderRepository(db)


def get_report_repo(db: AsyncSession = Depends(get_db)) -> DoctorReportRepository:
    """DoctorReportRepository dependency."""
    return DoctorReportRepository(db)


# ── Phase 3: Family ──────────────────────────────────────────
from backend.repositories.family_profile_repo import FamilyProfileRepository
from backend.repositories.subscription_repo import SubscriptionRepository
from backend.services.family_service import FamilyService

def get_family_repo(db: AsyncSession = Depends(get_db)) -> FamilyProfileRepository:
    return FamilyProfileRepository(db)

def get_subscription_repo(db: AsyncSession = Depends(get_db)) -> SubscriptionRepository:
    return SubscriptionRepository(db)

def get_family_service(
    family_repo: FamilyProfileRepository = Depends(get_family_repo),
    sub_repo: SubscriptionRepository = Depends(get_subscription_repo),
) -> FamilyService:
    return FamilyService(repo=family_repo, subscription_repo=sub_repo)

async def get_current_profile(
    profile_id: Optional[str] = Query(None, description="Profile ID (defaults to SELF)"),
    user_id: str = Depends(get_current_user),
    family_service: FamilyService = Depends(get_family_service),
) -> FamilyProfile:
    """Resolves profile_id param; defaults to SELF profile. Raises 404 if not owned."""
    return await family_service.get_profile_for_request(profile_id, user_id)

# require_tier: returns a Depends factory that raises FeatureNotAvailableError
def require_tier(min_tier: str):
    """FastAPI dependency factory that gates endpoints by subscription tier.
    Usage: Depends(require_tier('PREMIUM'))
    """
    TIER_ORDER = {'FREE': 0, 'PREMIUM': 1, 'PRO': 2}
    async def _check(
        user_id: str = Depends(get_current_user),
        sub_repo: SubscriptionRepository = Depends(get_subscription_repo),
    ):
        try:
            sub = await sub_repo.get_active_subscription(user_id)
            user_tier = sub.tier if sub else 'FREE'
        except Exception:
            user_tier = 'FREE'
        if TIER_ORDER.get(user_tier, 0) < TIER_ORDER.get(min_tier, 0):
            raise FeatureNotAvailableError(
                f'This feature requires {min_tier} subscription. '
                f'Upgrade at /api/subscription/upgrade'
            )
        return user_tier
    return _check


# ── Phase 3: Predictions ────────────────────────────────────
from backend.repositories.prediction_repo import PredictionRepository
from backend.services.prediction_service import PredictionService

def get_prediction_repo(db: AsyncSession = Depends(get_db)) -> PredictionRepository:
    return PredictionRepository(db)

def get_prediction_service(
    pred_repo: PredictionRepository = Depends(get_prediction_repo),
    param_repo: ClinicalParameterRepository = Depends(get_param_repo),
) -> PredictionService:
    return PredictionService(prediction_repo=pred_repo, param_repo=param_repo)

# ── Phase 3: ABDM / FHIR ────────────────────────────────────
from backend.adapters.abdm_adapter import MockABDMAdapter, ABDMAdapter
from backend.services.abdm_service import ABDMService

_abdm_adapter = MockABDMAdapter()

def get_abdm_adapter() -> ABDMAdapter: 
    return _abdm_adapter

def get_abdm_service(
    record_repo: HealthRecordRepository = Depends(get_record_repo), 
    param_repo: ClinicalParameterRepository = Depends(get_param_repo), 
    encryption_service: EncryptionService = Depends(get_encryption_service), 
    cache: ArogyaCache = Depends(get_cache), 
    adapter: ABDMAdapter = Depends(get_abdm_adapter)
) -> ABDMService:
    return ABDMService(adapter=adapter, encryption_service=encryption_service, record_repo=record_repo, param_repo=param_repo, cache=cache)

# ── Phase 3: Doctor Workspace ───────────────────────────────
from backend.repositories.doctor_access_repo import DoctorAccessRepository
from backend.services.doctor_workspace_service import DoctorWorkspaceService

def get_doctor_access_repo(db: AsyncSession = Depends(get_db)) -> DoctorAccessRepository: 
    return DoctorAccessRepository(db)

def get_doctor_workspace_service(
    access_repo: DoctorAccessRepository = Depends(get_doctor_access_repo), 
    record_repo: HealthRecordRepository = Depends(get_record_repo), 
    param_repo: ClinicalParameterRepository = Depends(get_param_repo), 
    risk_repo: RiskScoreRepository = Depends(get_risk_repo), 
    sub_repo: SubscriptionRepository = Depends(get_subscription_repo), 
    cfg: Settings = Depends(get_settings)
) -> DoctorWorkspaceService:
    return DoctorWorkspaceService(access_repo=access_repo, record_repo=record_repo, param_repo=param_repo, risk_repo=risk_repo, subscription_repo=sub_repo, settings=cfg)


# ── Phase 3: Wearables ────────────────────────────────────────
from backend.repositories.wearable_repo import WearableRepository
from backend.services.wearable_service import WearableService

def get_wearable_repo(db: AsyncSession = Depends(get_db), cache=Depends(get_cache)) -> WearableRepository: 
    return WearableRepository(db=db, cache=cache)

def get_wearable_service(repo=Depends(get_wearable_repo), enc=Depends(get_encryption_service), cache=Depends(get_cache), cfg=Depends(get_settings)) -> WearableService: 
    return WearableService(repo=repo, encryption_service=enc, cache=cache, settings=cfg)


# ── Phase 3: Subscription ────────────────────────────────────
from backend.services.subscription_service import SubscriptionService
from backend.adapters.razorpay_adapter import MockRazorpayAdapter, RazorpayAdapter

_razorpay_adapter = MockRazorpayAdapter()

def get_razorpay_adapter() -> RazorpayAdapter:
    return _razorpay_adapter

def get_subscription_service(
    repo=Depends(get_subscription_repo),
    razorpay=Depends(get_razorpay_adapter),
    cfg=Depends(get_settings),
) -> SubscriptionService:
    return SubscriptionService(repo=repo, razorpay=razorpay, settings=cfg)

# ── Phase 3: Health Score API ───────────────────────────────
from backend.repositories.api_key_repo import APIKeyRepository
from backend.services.health_api_service import HealthAPIService

def get_api_key_repo(db: AsyncSession = Depends(get_db)) -> APIKeyRepository: 
    return APIKeyRepository(db)

def get_health_api_service(
    api_key_repo=Depends(get_api_key_repo), 
    risk_repo=Depends(get_risk_repo), 
    param_repo=Depends(get_param_repo), 
    sub_repo=Depends(get_subscription_repo),
    family_repo=Depends(get_family_repo),
    cache=Depends(get_cache), 
    cfg=Depends(get_settings)
) -> HealthAPIService:
    return HealthAPIService(
        api_key_repo=api_key_repo, 
        risk_repo=risk_repo, 
        param_repo=param_repo, 
        subscription_repo=sub_repo, 
        family_repo=family_repo,
        cache=cache, 
        settings=cfg
    )

# -- Phase 3: WhatsApp Bot & Voice ------------------------
from backend.repositories.whatsapp_repo import WhatsAppRepository
from backend.services.whatsapp_service import WhatsAppBotService
from backend.services.voice_service import VoiceService

def get_whatsapp_repo(db: AsyncSession = Depends(get_db)) -> WhatsAppRepository:
    return WhatsAppRepository(db)

def get_whatsapp_service(
    wa_repo=Depends(get_whatsapp_repo),
    risk_repo=Depends(get_risk_repo),
    param_repo=Depends(get_param_repo),
    cache=Depends(get_cache),
    cfg=Depends(get_settings)
) -> WhatsAppBotService:
    return WhatsAppBotService(wa_repo=wa_repo, risk_repo=risk_repo, param_repo=param_repo, cache=cache, settings=cfg)

def get_voice_service(
    param_repo=Depends(get_param_repo),
    reminder_repo=Depends(get_reminder_repo),
    cache=Depends(get_cache),
    cfg=Depends(get_settings)
) -> VoiceService:
    return VoiceService(param_repo=param_repo, reminder_repo=reminder_repo, cache=cache, settings=cfg)
