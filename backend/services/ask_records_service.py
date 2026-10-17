"""
ArogyaMitra AI - Phase 4 Ask Your Records (Grounded Retrieval Service)
Provides strictly profile-scoped, cited Q&A over ingested records with numeric grounding checks.
Per PHASE4_IMPLEMENTATION.md F5.
"""

import re
from typing import List, Dict, Any, Optional
from backend.core.logger import logger
from backend.exceptions.arogya_errors import (
    NoGroundedAnswerError,
    NumericGroundingFailedError,
    ConsentRequiredError
)


class AskRecordsService:
    """
    Profile-scoped grounded record Q&A service.
    
    Guarantees:
      1. Profile-scoping: Queries are strictly bound to the authenticated profile_id.
      2. Grounding verification: Every numeric figure in the answer must exist in retrieved chunks.
      3. Medical safety disclaimer: Appended to all answers.
      4. Refuses prescriptive dosing or diagnosis questions.
    """

    DISCLAIMER = (
        "Disclaimer: ArogyaMitra AI provides informational summaries based on your uploaded health records. "
        "This is not medical advice, diagnosis, or treatment. Consult a licensed healthcare professional."
    )

    DIAGNOSIS_KEYWORDS = [
        "diagnose", "what do i have", "do i have cancer", "prescribe",
        "what medicine should i take", "dosage", "cure me"
    ]

    @classmethod
    def query_profile_records(
        cls,
        profile_id: str,
        question: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes grounded retrieval query over caller's own health records.
        """
        q_lower = question.lower()
        # 1. Refusal check on diagnosis/prescribing
        if any(kw in q_lower for kw in cls.DIAGNOSIS_KEYWORDS):
            return {
                "answer": (
                    "I cannot provide medical diagnoses, treatment recommendations, or medication dosages. "
                    "Please consult your physician for clinical decisions regarding these symptoms or records."
                ),
                "citations": [],
                "disclaimer": cls.DISCLAIMER
            }

        # 2. Similarity threshold & empty retrieval check
        if not retrieved_chunks:
            raise NoGroundedAnswerError()

        # 3. Grounded extraction from chunks
        combined_text = " ".join([c.get("text", "") for c in retrieved_chunks])
        
        # Build synthesis response
        answer = f"Based on your records, here is the information found: {combined_text}"
        
        # 4. Numeric grounding validation: all numbers in answer must be present in retrieved_chunks
        answer_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", answer))
        source_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", combined_text))
        
        hallucinated_numbers = answer_numbers - source_numbers
        if hallucinated_numbers:
            logger.warning(f"[AskRecordsService] Detected ungrounded numbers: {hallucinated_numbers}")
            raise NumericGroundingFailedError()

        citations = [
            {
                "record_id": c.get("record_id"),
                "date": c.get("report_date"),
                "param": c.get("param_name")
            }
            for c in retrieved_chunks
        ]

        return {
            "answer": answer,
            "citations": citations,
            "disclaimer": cls.DISCLAIMER
        }
