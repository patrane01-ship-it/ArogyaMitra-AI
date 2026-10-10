"""
ArogyaMitra AI - DoctorReport Schemas
Pydantic validation models for AI-generated doctor-prep reports.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class DoctorReportGenerateResponse(BaseModel):
    report_id: str
    generated_at: datetime
    preview: str
    pdf_ready: bool = True


class DoctorReportResponse(BaseModel):
    report_id: str
    user_id: str
    generated_at: datetime
    report_content: str
    records_included: List[str]
    share_token: Optional[str] = None
    share_expires_at: Optional[datetime] = None
    is_share_valid: bool = False

    class Config:
        from_attributes = True


class ShareTokenResponse(BaseModel):
    share_url: str
    expires_at: datetime
