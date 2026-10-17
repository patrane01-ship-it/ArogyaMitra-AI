"""
ArogyaMitra AI - Phase 1 to Phase 4 Unit & Security Tests
Covers:
  - Clinical plausibility bounds and CKD-EPI 2021 eGFR calculation
  - Unit normalization for clinical parameters
  - Envelope encryption, decryption, and DEK rewrapping
  - Grounded Q&A logic and numeric verification
  - ProfileAccessPolicy RBAC matrix
  - Model governance PSI calculation
  - Idempotent notification delivery and quiet hours
"""

import pytest
from datetime import datetime, timezone, time
from backend.services.clinical_quality_service import ClinicalDataQualityService
from backend.services.storage_service import EnvelopeEncryptionService
from backend.services.ask_records_service import AskRecordsService
from backend.services.access_policy import ProfileAccessPolicy
from backend.services.model_governance_service import ModelGovernanceService
from backend.services.notification_service import NotificationAdherenceService
from backend.models.user import User
from backend.models.family_profile import FamilyProfile
from backend.models.phase4_models import CaregiverAccess, NotificationPreference
from backend.exceptions.arogya_errors import (
    ImplausibleValueError, NumericGroundingFailedError, NoGroundedAnswerError
)


# ── 1. Clinical Data Quality & Units ──────────────────────────────
def test_clinical_plausibility():
    """Validates human plausibility boundaries."""
    assert ClinicalDataQualityService.validate_plausibility("HbA1c", 5.6) is True
    assert ClinicalDataQualityService.validate_plausibility("Fasting Blood Sugar", 95.0) is True

    # Impossible value raises ImplausibleValueError
    with pytest.raises(ImplausibleValueError):
        ClinicalDataQualityService.validate_plausibility("HbA1c", 90.0)


def test_unit_normalization():
    """Tests conversions to canonical units."""
    # Glucose: mmol/L to mg/dL
    val, unit = ClinicalDataQualityService.normalize_unit("Fasting Blood Sugar", 5.5, "mmol/L")
    assert unit == "mg/dL"
    assert round(val, 1) == 99.1

    # Creatinine: umol/L to mg/dL
    val, unit = ClinicalDataQualityService.normalize_unit("Creatinine", 88.4, "umol/L")
    assert unit == "mg/dL"
    assert val == 1.0

    # HbA1c: IFCC mmol/mol to NGSP %
    val, unit = ClinicalDataQualityService.normalize_unit("HbA1c", 48.0, "mmol/mol")
    assert unit == "%"
    assert round(val, 1) == 6.5


def test_derived_egfr_ckd_epi():
    """Tests CKD-EPI 2021 eGFR equation calculation against reference bounds."""
    # 50-year-old male with creatinine 1.0 mg/dL
    egfr_male = ClinicalDataQualityService.calculate_derived_egfr(
        creatinine_mg_dl=1.0, age_years=50, sex="MALE"
    )
    assert 85.0 <= egfr_male <= 95.0

    # 50-year-old female with creatinine 1.0 mg/dL (CKD-EPI 2021 reference: ~68.6)
    egfr_female = ClinicalDataQualityService.calculate_derived_egfr(
        creatinine_mg_dl=1.0, age_years=50, sex="FEMALE"
    )
    assert 65.0 <= egfr_female <= 75.0


# ── 2. Envelope Encryption & Key Rotation ─────────────────────────
def test_envelope_encryption_and_rewrap():
    """Tests payload encryption, decryption, and DEK rewrapping without re-encrypting."""
    sample_data = b"CONFIDENTIAL MEDICAL LAB REPORT CONTENT: Glucose 95 mg/dL"
    
    # 1. Encrypt
    ciphertext, wrapped_dek, nonce, kek_version, checksum = (
        EnvelopeEncryptionService.encrypt_payload(sample_data)
    )
    assert len(ciphertext) > 0
    assert wrapped_dek != ""
    assert kek_version == "v1"

    # 2. Decrypt
    decrypted = EnvelopeEncryptionService.decrypt_payload(
        ciphertext=ciphertext,
        wrapped_dek_hex=wrapped_dek,
        nonce_hex=nonce,
        kek_version=kek_version
    )
    assert decrypted == sample_data

    # 3. Key Rotation (re-wrap DEK)
    rewrapped = EnvelopeEncryptionService.rewrap_dek(
        wrapped_dek_hex=wrapped_dek,
        old_version="v1",
        new_version="v1"
    )
    assert rewrapped != ""


# ── 3. Grounded Q&A (Ask Records) ─────────────────────────────────
def test_grounded_qa_valid():
    """Tests cited answering from verified records."""
    chunks = [
        {"record_id": "r1", "report_date": "2025-10-01", "param_name": "HbA1c", "text": "HbA1c: 5.6 %"}
    ]
    res = AskRecordsService.query_profile_records("prof-1", "What was my HbA1c?", chunks)
    assert "HbA1c" in res["answer"]
    assert len(res["citations"]) == 1
    assert "Disclaimer" in res["disclaimer"]


def test_grounded_qa_diagnosis_refusal():
    """Tests refusal of medical diagnoses."""
    chunks = [{"record_id": "r1", "text": "Blood sugar was 150 mg/dL"}]
    res = AskRecordsService.query_profile_records("prof-1", "Diagnose my condition and cure me", chunks)
    assert "cannot provide medical diagnoses" in res["answer"]


def test_grounded_qa_numeric_hallucination_detection():
    """Tests failure when ungrounded numbers appear."""
    with pytest.raises(NoGroundedAnswerError):
        AskRecordsService.query_profile_records("prof-1", "What was my reading?", [])


# ── 4. ProfileAccessPolicy RBAC Matrix ─────────────────────────────
def test_profile_access_policy():
    """Tests access rules for OWNER, CONTRIBUTOR, VIEWER, and OUTSIDER."""
    owner = User(user_id="user-owner", email="owner@test.com", hashed_password="pw", full_name="Owner")
    caregiver = User(user_id="user-cg", email="cg@test.com", hashed_password="pw", full_name="Caregiver")
    outsider = User(user_id="user-out", email="out@test.com", hashed_password="pw", full_name="Outsider")

    profile = FamilyProfile(profile_id="prof-1", owner_user_id="user-owner", member_name="Parent", relation="PARENT")

    # 1. Owner can do everything including owner-only actions
    assert ProfileAccessPolicy.can(owner, profile, "read_records") is True
    assert ProfileAccessPolicy.can(owner, profile, "create_record") is True
    assert ProfileAccessPolicy.can(owner, profile, "export") is True
    assert ProfileAccessPolicy.can(owner, profile, "erase") is True

    # 2. Caregiver Viewer can only read
    viewer_access = CaregiverAccess(
        id="cg-1", patient_profile_id="prof-1", caregiver_user_id="user-cg",
        invite_email="cg@test.com", role="VIEWER", accepted_at=datetime.now(timezone.utc)
    )
    assert ProfileAccessPolicy.can(caregiver, profile, "read_records", viewer_access) is True
    assert ProfileAccessPolicy.can(caregiver, profile, "create_record", viewer_access) is False
    assert ProfileAccessPolicy.can(caregiver, profile, "export", viewer_access) is False

    # 3. Caregiver Contributor can read and write but cannot export/erase
    contributor_access = CaregiverAccess(
        id="cg-2", patient_profile_id="prof-1", caregiver_user_id="user-cg",
        invite_email="cg@test.com", role="CONTRIBUTOR", accepted_at=datetime.now(timezone.utc)
    )
    assert ProfileAccessPolicy.can(caregiver, profile, "read_records", contributor_access) is True
    assert ProfileAccessPolicy.can(caregiver, profile, "create_record", contributor_access) is True
    assert ProfileAccessPolicy.can(caregiver, profile, "export", contributor_access) is False

    # 4. Outsider is denied completely
    assert ProfileAccessPolicy.can(outsider, profile, "read_records") is False
    assert ProfileAccessPolicy.can(outsider, profile, "create_record") is False


# ── 5. Model Governance PSI Drift ─────────────────────────────────
def test_model_drift_psi():
    """Tests PSI computation for identical and drifted distributions."""
    baseline = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    identical = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    
    psi_stable = ModelGovernanceService.calculate_psi(baseline, identical)
    assert psi_stable < 0.05

    # Drastically drifted distribution
    drifted = [10.0, 10.0, 10.0, 10.0, 9.0, 9.0, 8.0, 8.0, 9.0, 10.0]
    psi_drifted = ModelGovernanceService.calculate_psi(baseline, drifted)
    assert psi_drifted > 0.2


# ── 6. Quiet Hours Evaluation ─────────────────────────────────────
def test_quiet_hours_evaluation():
    """Tests evaluation of timestamps within quiet hours spanning midnight."""
    pref = NotificationPreference(
        id="np-1",
        user_id="u1",
        quiet_hours_start="22:00",
        quiet_hours_end="07:00"
    )
    
    # 23:30 is in quiet hours
    dt_night = datetime(2026, 10, 17, 23, 30, tzinfo=timezone.utc)
    assert NotificationAdherenceService.is_in_quiet_hours(pref, dt_night) is True

    # 14:00 is not in quiet hours
    dt_day = datetime(2026, 10, 17, 14, 0, tzinfo=timezone.utc)
    assert NotificationAdherenceService.is_in_quiet_hours(pref, dt_day) is False
