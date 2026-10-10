"""
ArogyaMitra AI - ClinicalParameter Schemas
Pydantic validation models for clinical parameters.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ClinicalParameterBase(BaseModel):
    param_name: str
    value: float = Field(..., gt=0, description="Positive numeric test value")
    unit: str = Field(..., min_length=1)
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    report_date: datetime


class ClinicalParameterUpdate(BaseModel):
    value: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)


class ClinicalParameterResponse(BaseModel):
    param_id: str
    record_id: str
    param_name: str
    value: float
    unit: str
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    report_date: datetime
    status: str
    anomaly_score: Optional[float] = None

    class Config:
        from_attributes = True


class ParameterHistoryPoint(BaseModel):
    value: float
    report_date: datetime
    status: str
    anomaly_score: Optional[float] = None


class ParameterHistoryResponse(BaseModel):
    param_name: str
    unit: str
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    readings: List[ParameterHistoryPoint]
