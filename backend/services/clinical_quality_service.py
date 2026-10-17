"""
ArogyaMitra AI - Phase 4 Clinical Plausibility Bounds & Unit Canonicalization
Provides clinical reference boundaries and conversions to canonical units.
Per PHASE4_IMPLEMENTATION.md F6, F7.
"""

from typing import Tuple, Optional
from backend.exceptions.arogya_errors import ImplausibleValueError, UnknownUnitError


# Clinically plausible minimum and maximum bounds (flagging impossible data entry/OCR error)
PLAUSIBILITY_BOUNDS = {
    "HbA1c": (3.0, 25.0),
    "Fasting Blood Sugar": (20.0, 1000.0),
    "Total Cholesterol": (50.0, 1000.0),
    "LDL": (10.0, 800.0),
    "HDL": (5.0, 200.0),
    "Triglycerides": (20.0, 3000.0),
    "Hemoglobin": (2.0, 28.0),
    "Creatinine": (0.1, 30.0),
    "eGFR": (1.0, 200.0),
    "Blood Pressure Systolic": (40.0, 300.0),
    "Blood Pressure Diastolic": (20.0, 200.0),
    "TSH": (0.01, 150.0),
    "Vitamin D": (2.0, 250.0),
    "Vitamin B12": (25.0, 4000.0),
    "Uric Acid": (0.5, 30.0),
}


class ClinicalDataQualityService:
    """Service validating clinical plausibility and standardizing clinical units."""

    @classmethod
    def validate_plausibility(cls, param_name: str, value: float) -> bool:
        """
        Validates if parameter value is within physiological human limits.
        Raises ImplausibleValueError if value is outside physiological range.
        """
        bounds = PLAUSIBILITY_BOUNDS.get(param_name)
        if not bounds:
            return True

        min_val, max_val = bounds
        if value < min_val or value > max_val:
            raise ImplausibleValueError(
                f"{param_name} value {value} is outside plausible range ({min_val} - {max_val})"
            )
        return True

    @classmethod
    def normalize_unit(cls, param_name: str, value: float, unit: str) -> Tuple[float, str]:
        """
        Converts non-canonical units into standard canonical units.
        Returns: (normalized_value, canonical_unit)
        """
        u = unit.strip().lower()

        # Glucose: canonical mg/dL (mmol/L * 18.016)
        if param_name == "Fasting Blood Sugar":
            if u in {"mmol/l", "mmol/litre"}:
                return round(value * 18.016, 2), "mg/dL"
            elif u in {"mg/dl", "mg/100ml"}:
                return value, "mg/dL"

        # Lipids: canonical mg/dL
        elif param_name in {"Total Cholesterol", "LDL", "HDL"}:
            if u in {"mmol/l", "mmol/litre"}:
                return round(value * 38.67, 2), "mg/dL"
            elif u in {"mg/dl"}:
                return value, "mg/dL"

        elif param_name == "Triglycerides":
            if u in {"mmol/l", "mmol/litre"}:
                return round(value * 88.57, 2), "mg/dL"
            elif u in {"mg/dl"}:
                return value, "mg/dL"

        # Creatinine: canonical mg/dL (umol/L / 88.4)
        elif param_name == "Creatinine":
            if u in {"umol/l", "µmol/l", "micromol/l"}:
                return round(value / 88.4, 2), "mg/dL"
            elif u in {"mg/dl"}:
                return value, "mg/dL"

        # Uric Acid: canonical mg/dL (umol/L / 59.48)
        elif param_name == "Uric Acid":
            if u in {"umol/l", "µmol/l", "micromol/l"}:
                return round(value / 59.48, 2), "mg/dL"
            elif u in {"mg/dl"}:
                return value, "mg/dL"

        # Vitamin D: canonical ng/mL (nmol/L / 2.496)
        elif param_name == "Vitamin D":
            if u in {"nmol/l", "nmol/litre"}:
                return round(value / 2.496, 2), "ng/mL"
            elif u in {"ng/ml"}:
                return value, "ng/mL"

        # Vitamin B12: canonical pg/mL (pmol/L / 0.738)
        elif param_name == "Vitamin B12":
            if u in {"pmol/l", "pmol/litre"}:
                return round(value / 0.738, 2), "pg/mL"
            elif u in {"pg/ml"}:
                return value, "pg/mL"

        # Hemoglobin: canonical g/dL (g/L / 10)
        elif param_name == "Hemoglobin":
            if u in {"g/l", "g/litre"}:
                return round(value / 10.0, 2), "g/dL"
            elif u in {"g/dl"}:
                return value, "g/dL"

        # HbA1c: canonical % (NGSP) (from IFCC mmol/mol: % = mmol/mol / 10.929 + 2.15)
        elif param_name == "HbA1c":
            if u in {"mmol/mol"}:
                return round((value / 10.929) + 2.15, 2), "%"
            elif u in {"%"}:
                return value, "%"

        # Default fallback: keep original value and unit
        return value, unit

    @classmethod
    def calculate_derived_egfr(cls, creatinine_mg_dl: float, age_years: int, sex: str) -> float:
        """
        Computes estimated Glomerular Filtration Rate (eGFR) using the published CKD-EPI 2021 equation.
        eGFR = 142 * min(Scr/kappa, 1)**alpha * max(Scr/kappa, 1)**(-1.200) * 0.9938**Age * (1.012 if female)
        """
        is_female = (sex or "").upper() == "FEMALE"
        kappa = 0.7 if is_female else 0.9
        alpha = -0.241 if is_female else -0.302
        gender_factor = 1.012 if is_female else 1.0

        scr_over_k = creatinine_mg_dl / kappa
        min_factor = min(scr_over_k, 1.0) ** alpha
        max_factor = max(scr_over_k, 1.0) ** (-1.200)
        age_factor = 0.9938 ** age_years

        egfr = 142.0 * min_factor * max_factor * age_factor * gender_factor
        return round(egfr, 1)
