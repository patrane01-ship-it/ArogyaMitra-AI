"""
ArogyaMitra AI - Phase 4 ORM Entities
Models for Consent, Audit, Export, Erasure, Guardianship, Caregiver, Job queue,
Envelope file keys, Reference ranges, Notifications, and Account security.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship
from backend.database import Base


class PrivacyNoticeVersion(Base):
    __tablename__ = "privacy_notice_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(32), nullable=False, unique=True, index=True)
    language = Column(String(8), nullable=False, default="en")
    notice_text = Column(Text, nullable=False)
    text_hash = Column(String(64), nullable=False)
    effective_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(String(36), ForeignKey("family_profiles.profile_id", ondelete="CASCADE"), nullable=True, index=True)
    purpose = Column(String(64), nullable=False, index=True)  # CORE_SERVICE, AI_PROCESSING, WHATSAPP, WEARABLE_SYNC, ABDM_SYNC, DOCTOR_SHARING, RESEARCH_TRAINING, MARKETING
    granted = Column(Boolean, nullable=False, default=False)
    notice_version = Column(String(32), nullable=False)
    method = Column(String(32), nullable=False, default="WEB_UI")
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class GuardianConsent(Base):
    __tablename__ = "guardian_consents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("family_profiles.profile_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    guardian_user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    notice_version = Column(String(32), nullable=False)
    method = Column(String(64), nullable=False, default="SELF_ATTESTATION")
    attested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class DataExportJob(Base):
    __tablename__ = "data_export_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(String(36), ForeignKey("family_profiles.profile_id", ondelete="CASCADE"), nullable=True, index=True)
    format = Column(String(32), nullable=False, default="JSON")  # JSON, FHIR_BUNDLE, PDF_ZIP
    status = Column(String(32), nullable=False, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED, EXPIRED
    file_key = Column(String(255), nullable=True)
    download_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class ErasureRequest(Base):
    __tablename__ = "erasure_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    scope = Column(String(32), nullable=False, default="PROFILE")  # PROFILE, ACCOUNT
    profile_id = Column(String(36), ForeignKey("family_profiles.profile_id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), nullable=False, default="PENDING_GRACE")  # PENDING_GRACE, PROCESSING, COMPLETED, CANCELLED, FAILED
    grace_until = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_type = Column(String(32), nullable=False)  # USER, CAREGIVER, DOCTOR, SYSTEM, ADMIN
    actor_id = Column(String(36), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)
    target_type = Column(String(64), nullable=False)
    target_id = Column(String(64), nullable=True)
    profile_id = Column(String(36), nullable=True, index=True)
    request_id = Column(String(64), nullable=True)
    ip_hash = Column(String(64), nullable=True)
    occurred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class JobRecord(Base):
    __tablename__ = "job_records"

    job_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(64), nullable=False, index=True)
    owner_user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(String(36), ForeignKey("family_profiles.profile_id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="QUEUED", index=True)  # QUEUED, RUNNING, COMPLETED, FAILED, DEAD_LETTER
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    idempotency_key = Column(String(128), unique=True, nullable=True, index=True)
    payload = Column(JSON, nullable=True)
    last_error_code = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)


class StoredFileKey(Base):
    __tablename__ = "stored_file_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_key = Column(String(255), unique=True, nullable=False, index=True)
    wrapped_data_key = Column(Text, nullable=False)
    nonce = Column(String(64), nullable=False)
    kek_version = Column(String(32), nullable=False, index=True)
    checksum = Column(String(64), nullable=False)
    size_bytes = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class OCRCorrection(Base):
    __tablename__ = "ocr_corrections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    param_id = Column(String(36), ForeignKey("clinical_parameters.parameter_id", ondelete="CASCADE"), nullable=False, index=True)
    record_id = Column(String(36), ForeignKey("health_records.record_id", ondelete="CASCADE"), nullable=False, index=True)
    original_value = Column(Float, nullable=True)
    original_unit = Column(String(32), nullable=True)
    corrected_value = Column(Float, nullable=False)
    corrected_unit = Column(String(32), nullable=False)
    field_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ReferenceRangeProfile(Base):
    __tablename__ = "reference_range_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    param_name = Column(String(64), nullable=False, index=True)
    sex = Column(String(16), nullable=True)  # MALE, FEMALE, ALL
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    ref_min = Column(Float, nullable=False)
    ref_max = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False)
    source = Column(String(64), nullable=False, default="CLINICAL_STANDARD")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    channels = Column(JSON, nullable=False, default=lambda: ["IN_APP"])  # IN_APP, WEB_PUSH, WHATSAPP, EMAIL
    quiet_hours_start = Column(String(8), nullable=True)  # "22:00"
    quiet_hours_end = Column(String(8), nullable=True)    # "07:00"
    timezone = Column(String(64), nullable=False, default="Asia/Kolkata")
    show_medication_names = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(Text, nullable=False)
    encrypted_keys = Column(Text, nullable=False)
    user_agent = Column(String(255), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ReminderDelivery(Base):
    __tablename__ = "reminder_deliveries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reminder_id = Column(String(36), ForeignKey("reminders.reminder_id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=False, index=True)
    channel = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="SCHEDULED")  # SCHEDULED, DELIVERED, FAILED, SKIPPED_QUIET_HOURS
    attempts = Column(Integer, default=0, nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_unique_delivery", "reminder_id", "scheduled_for", "channel", unique=True),
    )


class AdherenceLog(Base):
    __tablename__ = "adherence_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reminder_id = Column(String(36), ForeignKey("reminders.reminder_id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(32), nullable=False)  # TAKEN, SKIPPED, SNOOZED, MISSED
    snooze_minutes = Column(Integer, nullable=True)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class CaregiverAccess(Base):
    __tablename__ = "caregiver_access"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_profile_id = Column(String(36), ForeignKey("family_profiles.profile_id", ondelete="CASCADE"), nullable=False, index=True)
    caregiver_user_id = Column(String(36), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    invite_email = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="VIEWER")  # VIEWER, CONTRIBUTOR
    scope = Column(JSON, nullable=False, default=lambda: ["READ_RECORDS", "READ_REMINDERS"])
    invite_token_hash = Column(String(64), nullable=False, unique=True, index=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class TotpSecret(Base):
    __tablename__ = "totp_secrets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    encrypted_secret = Column(Text, nullable=False)
    is_enabled = Column(Boolean, default=False, nullable=False)
    enabled_at = Column(DateTime(timezone=True), nullable=True)


class RecoveryCode(Base):
    __tablename__ = "recovery_codes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(64), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)


class UserSession(Base):
    __tablename__ = "user_sessions"

    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_family_id = Column(String(64), nullable=False, index=True)
    device_label = Column(String(255), nullable=True)
    ip_hash = Column(String(64), nullable=True)
    last_used_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(64), nullable=False, default="GENERAL")
    message = Column(Text, nullable=False)
    screen = Column(String(64), nullable=True)
    can_contact = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class DriftReport(Base):
    __tablename__ = "drift_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String(64), nullable=False, index=True)
    metrics_json = Column(JSON, nullable=False)
    data_source = Column(String(64), nullable=False, default="PRODUCTION")
    psi_by_feature = Column(JSON, nullable=False)
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
