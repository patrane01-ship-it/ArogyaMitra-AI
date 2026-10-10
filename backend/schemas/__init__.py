"""
ArogyaMitra AI - Pydantic Schemas Package
"""

from backend.schemas.health_record_schema import (
    HealthRecordBase,
    HealthRecordUpdate,
    HealthRecordManualCreate,
    HealthRecordResponse,
    HealthRecordUploadResponse,
)
from backend.schemas.clinical_parameter_schema import (
    ClinicalParameterBase,
    ClinicalParameterUpdate,
    ClinicalParameterResponse,
    ParameterHistoryPoint,
    ParameterHistoryResponse,
)
from backend.schemas.risk_score_schema import (
    RiskScoreResponse,
    RiskScoreNoDataResponse,
)
from backend.schemas.reminder_schema import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse,
)
from backend.schemas.doctor_report_schema import (
    DoctorReportGenerateResponse,
    DoctorReportResponse,
    ShareTokenResponse,
)
from backend.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    ProfileUpdateRequest,
    ChangePasswordRequest,
    RegisterResponse,
    TokenResponse,
    RefreshResponse,
    UserProfileResponse,
    LogoutResponse,
    MessageResponse,
)

__all__ = [
    "HealthRecordBase",
    "HealthRecordUpdate",
    "HealthRecordManualCreate",
    "HealthRecordResponse",
    "HealthRecordUploadResponse",
    "ClinicalParameterBase",
    "ClinicalParameterUpdate",
    "ClinicalParameterResponse",
    "ParameterHistoryPoint",
    "ParameterHistoryResponse",
    "RiskScoreResponse",
    "RiskScoreNoDataResponse",
    "ReminderCreate",
    "ReminderUpdate",
    "ReminderResponse",
    "DoctorReportGenerateResponse",
    "DoctorReportResponse",
    "ShareTokenResponse",
    # Phase 2 Auth
    "RegisterRequest",
    "LoginRequest",
    "RefreshRequest",
    "ProfileUpdateRequest",
    "ChangePasswordRequest",
    "RegisterResponse",
    "TokenResponse",
    "RefreshResponse",
    "UserProfileResponse",
    "LogoutResponse",
    "MessageResponse",
]
