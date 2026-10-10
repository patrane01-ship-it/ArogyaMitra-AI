"""
ArogyaMitra AI - Drug Interaction Service (Phase 2)
CSV-based drug interaction lookup with fuzzy string matching.
Per FEATURES_PHASE2.md §2.4 and TECH_STACK_PHASE2.md §5.
"""

import os
import csv
import difflib
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache

from backend.config import settings
from backend.core.logger import logger
from backend.exceptions.arogya_errors import (
    SameDrugInteractionError,
    UnrecognizedDrugError,
    InvalidSeverityError,
)

VALID_SEVERITY_LEVELS = {"mild", "moderate", "severe", "contraindicated"}


class DrugInteractionService:
    """
    Checks drug-drug interactions using a local CSV database.
    Falls back to a curated known-interactions dictionary if CSV not loaded.
    """

    # Class-level drug database
    _drug_db: List[Dict[str, str]] = []
    _drug_names: List[str] = []
    _db_loaded: bool = False

    # Fallback known interactions (curated clinical pairs)
    _KNOWN_INTERACTIONS: Dict[Tuple[str, str], Dict[str, str]] = {
        ("warfarin", "aspirin"): {
            "severity": "severe",
            "description": "Increased bleeding risk. Co-administration significantly elevates hemorrhage risk.",
            "recommendation": "Avoid combination. If necessary, monitor INR closely and adjust warfarin dose.",
        },
        ("metformin", "alcohol"): {
            "severity": "moderate",
            "description": "Increased risk of lactic acidosis with heavy alcohol use.",
            "recommendation": "Limit alcohol intake. Monitor for lactic acidosis symptoms.",
        },
        ("simvastatin", "amiodarone"): {
            "severity": "severe",
            "description": "Risk of myopathy and rhabdomyolysis due to CYP3A4 inhibition.",
            "recommendation": "Limit simvastatin dose to 20 mg/day when co-administered with amiodarone.",
        },
        ("lisinopril", "potassium"): {
            "severity": "moderate",
            "description": "ACE inhibitors reduce potassium excretion; hyperkalemia risk.",
            "recommendation": "Monitor serum potassium regularly. Avoid high-potassium supplements.",
        },
        ("ssri", "maoi"): {
            "severity": "contraindicated",
            "description": "Serotonin syndrome risk — potentially fatal.",
            "recommendation": "Do not co-administer. Allow 14-day washout period.",
        },
        ("clopidogrel", "omeprazole"): {
            "severity": "moderate",
            "description": "Omeprazole inhibits CYP2C19, reducing clopidogrel's antiplatelet effect.",
            "recommendation": "Consider alternative PPI (e.g., pantoprazole) if antiplatelet therapy is critical.",
        },
        ("digoxin", "amiodarone"): {
            "severity": "severe",
            "description": "Amiodarone significantly increases digoxin plasma concentration.",
            "recommendation": "Reduce digoxin dose by 30-50% and monitor digoxin levels.",
        },
        ("methotrexate", "nsaids"): {
            "severity": "severe",
            "description": "NSAIDs reduce renal clearance of methotrexate, risk of toxicity.",
            "recommendation": "Avoid concurrent use, especially at high-dose methotrexate.",
        },
    }

    @classmethod
    def load_drug_db(cls, csv_path: Optional[str] = None) -> bool:
        """Load drug interaction CSV database. Returns True if successful."""
        path = csv_path or settings.DRUG_DB_CSV_PATH
        if not os.path.exists(path):
            logger.warning(f"[DrugDB] CSV not found at {path}. Using built-in interaction list.")
            cls._db_loaded = False
            return False

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                cls._drug_db = list(reader)
            cls._drug_names = list({
                row.get("drug_name", "").lower().strip()
                for row in cls._drug_db
                if row.get("drug_name")
            })
            cls._db_loaded = True
            logger.info(f"[DrugDB] Loaded {len(cls._drug_db)} entries, {len(cls._drug_names)} unique drugs")
            return True
        except Exception as e:
            logger.error(f"[DrugDB] Failed to load CSV: {e}")
            cls._db_loaded = False
            return False

    @classmethod
    def _fuzzy_match_drug(cls, drug_name: str) -> Optional[str]:
        """
        Find best fuzzy match for drug name in the loaded database.
        Returns closest match if score ≥ 0.6, else None.
        """
        query = drug_name.lower().strip()

        if cls._db_loaded and cls._drug_names:
            matches = difflib.get_close_matches(query, cls._drug_names, n=1, cutoff=0.6)
            return matches[0] if matches else None

        # Search fallback known interactions
        all_names = set()
        for k in cls._KNOWN_INTERACTIONS:
            all_names.add(k[0])
            all_names.add(k[1])
        matches = difflib.get_close_matches(query, list(all_names), n=1, cutoff=0.6)
        return matches[0] if matches else None

    @classmethod
    def check_interaction(
        cls,
        drug_a: str,
        drug_b: str,
    ) -> Dict[str, Any]:
        """
        Check for known interactions between two drugs.

        Returns:
            {
                "drug_a": str,
                "drug_b": str,
                "resolved_a": str,
                "resolved_b": str,
                "interaction_found": bool,
                "severity": str | None,
                "description": str | None,
                "recommendation": str | None,
                "source": "csv" | "builtin" | "none",
            }
        """
        if not drug_a or not drug_b:
            raise UnrecognizedDrugError("Both drug names must be provided")

        drug_a_clean = drug_a.strip().lower()
        drug_b_clean = drug_b.strip().lower()

        if drug_a_clean == drug_b_clean:
            raise SameDrugInteractionError()

        resolved_a = cls._fuzzy_match_drug(drug_a_clean) or drug_a_clean
        resolved_b = cls._fuzzy_match_drug(drug_b_clean) or drug_b_clean

        # Check CSV database first
        if cls._db_loaded and cls._drug_db:
            for row in cls._drug_db:
                row_drug = (row.get("drug_name") or "").lower().strip()
                interacts_with = (row.get("interacts_with") or "").lower().strip()
                if (
                    (row_drug in (resolved_a, drug_a_clean) and interacts_with in (resolved_b, drug_b_clean))
                    or (row_drug in (resolved_b, drug_b_clean) and interacts_with in (resolved_a, drug_a_clean))
                ):
                    severity = row.get("severity", "unknown").lower()
                    return {
                        "drug_a": drug_a,
                        "drug_b": drug_b,
                        "resolved_a": resolved_a,
                        "resolved_b": resolved_b,
                        "interaction_found": True,
                        "severity": severity,
                        "description": row.get("description", "Interaction noted."),
                        "recommendation": row.get("recommendation", "Consult a physician."),
                        "source": "csv",
                    }

        # Check built-in interaction dictionary
        key = (resolved_a, resolved_b)
        reverse_key = (resolved_b, resolved_a)
        interaction = cls._KNOWN_INTERACTIONS.get(key) or cls._KNOWN_INTERACTIONS.get(reverse_key)

        if interaction:
            return {
                "drug_a": drug_a,
                "drug_b": drug_b,
                "resolved_a": resolved_a,
                "resolved_b": resolved_b,
                "interaction_found": True,
                "severity": interaction["severity"],
                "description": interaction["description"],
                "recommendation": interaction["recommendation"],
                "source": "builtin",
            }

        # No interaction found
        logger.info(f"[DrugDB] No known interaction: {resolved_a} ↔ {resolved_b}")
        return {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "resolved_a": resolved_a,
            "resolved_b": resolved_b,
            "interaction_found": False,
            "severity": None,
            "description": "No known interaction found in database.",
            "recommendation": "Always consult a healthcare professional before combining medications.",
            "source": "none",
        }

    @classmethod
    def batch_check(
        cls,
        drug_list: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Check all pairwise interactions for a list of drugs.
        Returns a list of interaction results for each unique pair.
        """
        results = []
        drugs = [d.strip() for d in drug_list if d.strip()]
        for i in range(len(drugs)):
            for j in range(i + 1, len(drugs)):
                try:
                    result = cls.check_interaction(drugs[i], drugs[j])
                    results.append(result)
                except SameDrugInteractionError:
                    pass  # skip duplicates
                except Exception as e:
                    logger.warning(f"[DrugDB] Batch check error for {drugs[i]}/{drugs[j]}: {e}")
        return results
