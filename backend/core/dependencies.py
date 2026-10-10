"""
ArogyaMitra AI - Dependency Injection Registry
Central repository for FastAPI dependencies.
Per PRODUCTION_BACKEND.md §5.1 and FEATURES_PHASE2.md §2.1.
"""

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
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
