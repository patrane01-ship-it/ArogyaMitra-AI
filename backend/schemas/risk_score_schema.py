"""
ArogyaMitra AI - RiskScore Schemas
Pydantic validation models for risk score and health intelligence ratings.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RiskScoreResponse(BaseModel):
    score_id: str
    user_id: str
    computed_at: datetime
    overall_risk: float = Field(..., ge=0.0, le=1.0)
    risk_level: str
    contributing_factors: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    version: int

    class Config:
        from_attributes = True


class RiskScoreNoDataResponse(BaseModel):
    status: str = "no_data"
    message: str = "Upload your first report to see your health score"
