"""
ArogyaMitra AI - HealthRecord Schemas
Pydantic validation models for HealthRecord endpoints.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HealthRecordBase(BaseModel):
    record_type: str = Field(..., description="LAB_REPORT, PRESCRIPTION, DOCTOR_NOTE, IMAGING, MANUAL_ENTRY")
    report_date: datetime


class HealthRecordUpdate(BaseModel):
    record_type: Optional[str] = None
    report_date: Optional[datetime] = None


class HealthRecordManualCreate(BaseModel):
    record_type: str = "MANUAL_ENTRY"
    report_date: datetime
    parameters: List[Dict[str, Any]] = []
    notes: Optional[str] = None


class HealthRecordResponse(BaseModel):
    record_id: str
    user_id: str
    record_type: str
    upload_date: datetime
    report_date: datetime
    is_processed: bool
    is_deleted: bool
    extracted_entities: Optional[Dict[str, Any]] = None
    share_token: Optional[str] = None
    share_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthRecordUploadResponse(BaseModel):
    record_id: str
    status: str
    message: str
