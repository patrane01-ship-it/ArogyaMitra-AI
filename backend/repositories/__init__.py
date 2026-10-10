"""
ArogyaMitra AI - Repositories Package
Exports repository classes for all domain models.
"""

from backend.repositories.health_record_repo import HealthRecordRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.repositories.risk_score_repo import RiskScoreRepository
from backend.repositories.reminder_repo import ReminderRepository
from backend.repositories.doctor_report_repo import DoctorReportRepository

__all__ = [
    "HealthRecordRepository",
    "ClinicalParameterRepository",
    "RiskScoreRepository",
    "ReminderRepository",
    "DoctorReportRepository",
]
