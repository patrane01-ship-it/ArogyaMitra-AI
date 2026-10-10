"""
ArogyaMitra AI - Clinical Entity Extractor
Extracts clinical parameters from raw text using regex patterns with Groq LLM fallback.
Enforces prompt sanitization, hardened system prompts, and strict output schema validation.
Per PRODUCTION_BACKEND.md §7.2, §7.3, §7.4 and TECH_STACK.md §1.
"""

import re
import json
from typing import List, Dict, Any, Optional
from backend.config import SUPPORTED_PARAMETERS, settings
from backend.core.logger import logger
from backend.core.prompt_guard import sanitize_for_prompt
from backend.core.prompt_templates import ENTITY_EXTRACTION_SYSTEM


# Regex pattern aliases for the 15 supported parameters
PARAM_PATTERNS = {
    "HbA1c": [
        r"(?:hba1c|glycated\s+hemoglobin|glycosylated\s+hemoglobin)[\s:\-=]+(\d+(?:\.\d+)?)\s*(%?)",
    ],
    "Fasting Blood Sugar": [
        r"(?:fasting\s+blood\s+(?:sugar|glucose)|fbs|glucose[\s,]+fasting)[\s:\-=]+(\d+(?:\.\d+)?)\s*(mg/dl)?",
    ],
    "Total Cholesterol": [
        r"(?:total\s+cholesterol|serum\s+cholesterol)[\s:\-=]+(\d+(?:\.\d+)?)\s*(mg/dl)?",
    ],
    "LDL": [
        r"(?:ldl\s+cholesterol|ldl[\s\-]+c|ldl)[\s:\-=]+(\d+(?:\.\d+)?)\s*(mg/dl)?",
    ],
    "HDL": [
        r"(?:hdl\s+cholesterol|hdl[\s\-]+c|hdl)[\s:\-=]+(\d+(?:\.\d+)?)\s*(mg/dl)?",
    ],
    "Triglycerides": [
        r"(?:triglycerides|serum\s+triglycerides|tg)[\s:\-=]+(\d+(?:\.\d+)?)\s*(mg/dl)?",
    ],
    "Hemoglobin": [
        r"(?:hemoglobin|haemoglobin|hb)[\s:\-=]+(\d+(?:\.\d+)?)\s*(g/dl|gm/dl)?",
    ],
    "Creatinine": [
        r"(?:serum\s+creatinine|creatinine)[\s:\-=]+(\d+(?:\.\d+)?)\s*(mg/dl)?",
    ],
    "eGFR": [
        r"(?:egfr|estimated\s+gfr)[\s:\-=]+(\d+(?:\.\d+)?)\s*(ml/min(?:/1\.73m²|/1\.73m2)?)?",
    ],
    "Blood Pressure Systolic": [
        r"(?:bp|blood\s+pressure)[\s:\-=]+(\d{2,3})\s*/\s*(\d{2,3})",
        r"(?:systolic\s+bp|systolic)[\s:\-=]+(\d{2,3})\s*(mmhg)?",
    ],
    "Blood Pressure Diastolic": [
        r"(?:diastolic\s+bp|diastolic)[\s:\-=]+(\d{2,3})\s*(mmhg)?",
    ],
    "TSH": [
        r"(?:tsh|thyroid\s+stimulating\s+hormone)[\s:\-=]+(\d+(?:\.\d+)?)\s*(miu/l|uIU/ml)?",
    ],
    "Vitamin D": [
        r"(?:vitamin\s+d(?:3)?|25[\s\-]+hydroxy\s+vitamin\s+d)[\s:\-=]+(\d+(?:\.\d+)?)\s*(ng/ml)?",
    ],
    "Vitamin B12": [
        r"(?:vitamin\s+b12|b12|cyanocobalamin)[\s:\-=]+(\d+(?:\.\d+)?)\s*(pg/ml)?",
    ],
    "Uric Acid": [
        r"(?:serum\s+uric\s+acid|uric\s+acid)[\s:\-=]+(\d+(?:\.\d+)?)\s*(mg/dl)?",
    ]
}


class EntityExtractor:
    """Extracts clinical entities using regex and Groq LLM fallback."""

    def __init__(self, groq_client=None):
        self._groq_client = groq_client

    def _get_groq_client(self):
        if self._groq_client is None and settings.GROQ_API_KEY:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                logger.warning(f"[EntityExtractor] Groq initialization skipped: {e}")
        return self._groq_client

    def extract_with_regex(self, text: str) -> List[Dict[str, Any]]:
        """Extract parameters via rule-based regular expressions."""
        results = []
        found_names = set()

        for param_name, patterns in PARAM_PATTERNS.items():
            if param_name in found_names:
                continue

            config = SUPPORTED_PARAMETERS.get(param_name, {})
            default_unit = config.get("unit", "")
            ref_min = config.get("ref_min")
            ref_max = config.get("ref_max")

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if param_name == "Blood Pressure Systolic" and "/" in match.group(0):
                        # Matched combined BP (e.g. 120/80)
                        try:
                            sys_val = float(match.group(1))
                            dia_val = float(match.group(2))
                            results.append({
                                "name": "Blood Pressure Systolic",
                                "value": sys_val,
                                "unit": "mmHg",
                                "ref_min": SUPPORTED_PARAMETERS["Blood Pressure Systolic"]["ref_min"],
                                "ref_max": SUPPORTED_PARAMETERS["Blood Pressure Systolic"]["ref_max"],
                            })
                            results.append({
                                "name": "Blood Pressure Diastolic",
                                "value": dia_val,
                                "unit": "mmHg",
                                "ref_min": SUPPORTED_PARAMETERS["Blood Pressure Diastolic"]["ref_min"],
                                "ref_max": SUPPORTED_PARAMETERS["Blood Pressure Diastolic"]["ref_max"],
                            })
                            found_names.add("Blood Pressure Systolic")
                            found_names.add("Blood Pressure Diastolic")
                            break
                        except Exception:
                            continue

                    try:
                        val = float(match.group(1))
                        unit = match.group(2) if len(match.groups()) >= 2 and match.group(2) else default_unit
                        results.append({
                            "name": param_name,
                            "value": val,
                            "unit": unit or default_unit,
                            "ref_min": ref_min,
                            "ref_max": ref_max,
                        })
                        found_names.add(param_name)
                        break
                    except (ValueError, IndexError):
                        continue

        return results

    def extract_with_groq(self, text: str) -> List[Dict[str, Any]]:
        """Fallback extractor using Groq LLM with strict output verification."""
        client = self._get_groq_client()
        if not client:
            logger.warning("[EntityExtractor] Groq client unavailable for LLM extraction")
            return []

        # Sanitize prompt before calling LLM
        safe_text = sanitize_for_prompt(text, max_chars=3000)

        prompt = (
            f"Extract clinical parameters from the following medical report text:\n\n"
            f"--- REPORT TEXT ---\n{safe_text}\n--- END REPORT ---\n\n"
            f"Remember: Output ONLY valid JSON matching schema: "
            f'{{"parameters": [{{"name": str, "value": float, "unit": str, "ref_min": float, "ref_max": float}}]}}'
        )

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": ENTITY_EXTRACTION_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            raw_content = response.choices[0].message.content.strip()

            # Output validation per §7.4
            # 1. Clean markdown code blocks
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw_content)
            cleaned = re.sub(r"\s*```$", "", cleaned).strip()

            # 2. Parse JSON
            data = json.loads(cleaned)

            # 3. Validate schema
            params_raw = data.get("parameters", [])
            if not isinstance(params_raw, list):
                return []

            valid_params = []
            for item in params_raw:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                val = item.get("value")
                unit = item.get("unit")

                # Match against SUPPORTED_PARAMETERS (case insensitive mapping)
                matched_name = None
                for supp in SUPPORTED_PARAMETERS.keys():
                    if supp.lower() == str(name).lower() or str(name).lower() in supp.lower():
                        matched_name = supp
                        break

                if not matched_name:
                    continue

                try:
                    num_val = float(val)
                    if num_val <= 0:
                        continue
                except (ValueError, TypeError):
                    continue

                config = SUPPORTED_PARAMETERS[matched_name]
                valid_params.append({
                    "name": matched_name,
                    "value": num_val,
                    "unit": str(unit) if unit else config["unit"],
                    "ref_min": item.get("ref_min", config.get("ref_min")),
                    "ref_max": item.get("ref_max", config.get("ref_max")),
                })

            # 4. Cap at 20 parameters per document
            return valid_params[:20]

        except Exception as e:
            logger.warning(f"[EntityExtractor] Groq LLM extraction failed: {e}")
            return []

    def extract(self, text: str) -> List[Dict[str, Any]]:
        """
        Master extraction pipeline:
        1. Run regex extractor.
        2. If regex finds fewer than 2 parameters and text length > 50, run Groq fallback.
        3. Merge results without duplicates.
        """
        regex_results = self.extract_with_regex(text)
        
        if len(regex_results) < 2 and len(text.strip()) > 50 and settings.GROQ_API_KEY:
            logger.info("[EntityExtractor] Regex found few parameters. Invoking Groq fallback.")
            groq_results = self.extract_with_groq(text)
            
            # Merge: regex results take precedence
            seen_names = {p["name"] for p in regex_results}
            for p in groq_results:
                if p["name"] not in seen_names:
                    regex_results.append(p)
                    seen_names.add(p["name"])

        return regex_results
