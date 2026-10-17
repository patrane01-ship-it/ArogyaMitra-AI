"""
ArogyaMitra AI - ORM Models Package
Exports Base and all Phase 1, Phase 2, Phase 3, and Phase 4 entities for SQLAlchemy and Alembic migrations.
"""

from backend.database import Base
from backend.models.health_record import HealthRecord, RecordType
from backend.models.clinical_parameter import ClinicalParameter, ParameterStatus
from backend.models.risk_score import RiskScore, RiskLevel
from backend.models.reminder import Reminder, ReminderType, RecurrenceType
from backend.models.doctor_report import DoctorReport
from backend.models.user import User
from backend.models.ml_risk_model import MLRiskModel
from backend.models.anomaly_result import AnomalyResult
from backend.models.drug_interaction import DrugInteraction, InteractionSeverity

# Phase 3 Models
from backend.models.family_profile import FamilyProfile
from backend.models.subscription_tier import SubscriptionTier
from backend.models.prediction_result import PredictionResult
from backend.models.doctor_access import DoctorAccess
from backend.models.wearable_reading import WearableReading
from backend.models.whatsapp_session import WhatsAppSession
from backend.models.api_key import APIKey

# Phase 4 Models
from backend.models.phase4_models import (
    PrivacyNoticeVersion,
    ConsentRecord,
    GuardianConsent,
    DataExportJob,
    ErasureRequest,
    AuditLogEntry,
    JobRecord,
    StoredFileKey,
    OCRCorrection,
    ReferenceRangeProfile,
    NotificationPreference,
    PushSubscription,
    ReminderDelivery,
    AdherenceLog,
    CaregiverAccess,
    EmailVerificationToken,
    PasswordResetToken,
    TotpSecret,
    RecoveryCode,
    UserSession,
    FeedbackEntry,
    DriftReport,
)

__all__ = [
    "Base",
    "HealthRecord",
    "RecordType",
    "ClinicalParameter",
    "ParameterStatus",
    "RiskScore",
    "RiskLevel",
    "Reminder",
    "ReminderType",
    "RecurrenceType",
    "DoctorReport",
    "User",
    "MLRiskModel",
    "AnomalyResult",
    "DrugInteraction",
    "InteractionSeverity",
    # Phase 3
    "FamilyProfile",
    "SubscriptionTier",
    "PredictionResult",
    "DoctorAccess",
    "WearableReading",
    "WhatsAppSession",
    "APIKey",
    # Phase 4
    "PrivacyNoticeVersion",
    "ConsentRecord",
    "GuardianConsent",
    "DataExportJob",
    "ErasureRequest",
    "AuditLogEntry",
    "JobRecord",
    "StoredFileKey",
    "OCRCorrection",
    "ReferenceRangeProfile",
    "NotificationPreference",
    "PushSubscription",
    "ReminderDelivery",
    "AdherenceLog",
    "CaregiverAccess",
    "EmailVerificationToken",
    "PasswordResetToken",
    "TotpSecret",
    "RecoveryCode",
    "UserSession",
    "FeedbackEntry",
    "DriftReport",
]
