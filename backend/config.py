"""
ArogyaMitra AI - Configuration Settings
Loads environment variables and provides application constants.
"""

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str
    
    # ── Cache (Redis) ───────────────────────────────────
    REDIS_URL: str
    
    # ── LLM ─────────────────────────────────────────────
    GROQ_API_KEY: str
    
    # ── Security ───────────────────────────────────────
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    
    # ── App ─────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: str = '["http://localhost:5173"]'
    
    # ── Storage ─────────────────────────────────────────
    UPLOAD_DIR: str = "./backend/data/records/encrypted"
    CHROMA_DB_PATH: str = "./backend/data/chroma_db"
    
    # ── Phase 2 Settings: Auth, ML & Drug DB ────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    DRUG_DB_CSV_PATH: str = "./backend/data/drug_db/drugbank_open.csv"
    ML_MODELS_DIR: str = "./backend/ml/models"
    ACTIVE_MODEL_PATH: str = "./backend/ml/models/risk_model_v2.pkl"
    ANOMALY_THRESHOLD: float = -0.1
    ANOMALY_CONTAMINATION: float = 0.1
    DRUG_INTERACTION_DISTANCE_THRESHOLD: float = 0.35
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS from JSON string to list."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except json.JSONDecodeError:
            return ["http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# ── SUPPORTED PARAMETERS (from TECH_STACK.md) ─────────────
# Reference ranges for common clinical parameters
SUPPORTED_PARAMETERS = {
    "HbA1c": {
        "unit": "%",
        "ref_min": 4.0,
        "ref_max": 5.7,
        "critical_threshold": 7.0
    },
    "Fasting Blood Sugar": {
        "unit": "mg/dL",
        "ref_min": 70,
        "ref_max": 100,
        "critical_threshold": 126
    },
    "Total Cholesterol": {
        "unit": "mg/dL",
        "ref_min": 0,
        "ref_max": 200,
        "critical_threshold": 240
    },
    "LDL": {
        "unit": "mg/dL",
        "ref_min": 0,
        "ref_max": 100,
        "critical_threshold": 160
    },
    "HDL": {
        "unit": "mg/dL",
        "ref_min": 40,
        "ref_max": 60,
        "critical_threshold": None  # Low HDL is concern, not high
    },
    "Triglycerides": {
        "unit": "mg/dL",
        "ref_min": 0,
        "ref_max": 150,
        "critical_threshold": 200
    },
    "Hemoglobin": {
        "unit": "g/dL",
        "ref_min": 12.0,
        "ref_max": 16.0,
        "critical_threshold": 8.0
    },
    "Creatinine": {
        "unit": "mg/dL",
        "ref_min": 0.6,
        "ref_max": 1.2,
        "critical_threshold": 2.0
    },
    "eGFR": {
        "unit": "mL/min/1.73m²",
        "ref_min": 60,
        "ref_max": 120,
        "critical_threshold": 30
    },
    "Blood Pressure Systolic": {
        "unit": "mmHg",
        "ref_min": 90,
        "ref_max": 120,
        "critical_threshold": 140
    },
    "Blood Pressure Diastolic": {
        "unit": "mmHg",
        "ref_min": 60,
        "ref_max": 80,
        "critical_threshold": 90
    },
    "TSH": {
        "unit": "mIU/L",
        "ref_min": 0.4,
        "ref_max": 4.0,
        "critical_threshold": 10.0
    },
    "Vitamin D": {
        "unit": "ng/mL",
        "ref_min": 20,
        "ref_max": 50,
        "critical_threshold": 10
    },
    "Vitamin B12": {
        "unit": "pg/mL",
        "ref_min": 200,
        "ref_max": 900,
        "critical_threshold": 150
    },
    "Uric Acid": {
        "unit": "mg/dL",
        "ref_min": 2.4,
        "ref_max": 6.0,
        "critical_threshold": 7.0
    }
}


# ── Constants ─────────────────────────────────────────────
OCR_MIN_TEXT_LENGTH = 20  # Minimum characters to consider OCR successful
MAX_FILE_SIZE_MB = 10
ALLOWED_MIME_TYPES = ["application/pdf", "image/jpeg", "image/png"]
