"""
ArogyaMitra AI - Guardrails
Output validation rules to block prescriptive medication advice, unauthorized diagnosis,
PII leakage, and prompt injection echoing.
Per PRODUCTION_BACKEND.md §8.1.
"""

import re
from backend.core.logger import logger
from backend.exceptions.arogya_errors import GuardrailViolationError

OUTPUT_GUARDRAILS = [
    # Medical safety guardrails
    {
        "pattern": r"you\s+(should|must|need to)\s+(take|stop taking|increase|decrease)\s+\w+",
        "reason": "Prescriptive medication advice",
        "action": "strip_and_warn"
    },
    {
        "pattern": r"(diagnosis|diagnose|you have|you are suffering from)",
        "reason": "Diagnosis claim",
        "action": "strip_and_warn"
    },
    # PII leakage guardrails
    {
        "pattern": r"\b\d{10}\b",
        "reason": "Possible phone number in output",
        "action": "redact"
    },
    {
        "pattern": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}",
        "reason": "Email address in output",
        "action": "redact"
    },
    # Injection echo guardrails (model echoing injected instructions)
    {
        "pattern": r"ignore\s+(all\s+)?previous\s+instructions?",
        "reason": "Injection echo in output",
        "action": "block"
    },
]


def apply_output_guardrails(text: str, context: str = "general") -> str:
    """
    Applies guardrails to LLM output:
    - block: Raises GuardrailViolationError
    - strip_and_warn: Strips prescriptive medical advice
    - redact: Redacts phone/email PII
    """
    if not text:
        return ""

    sanitized = text
    for rule in OUTPUT_GUARDRAILS:
        matches = re.findall(rule["pattern"], sanitized, re.IGNORECASE)
        if matches:
            logger.warning(
                f"[Guardrail] TRIGGERED | reason={rule['reason']} | context={context}"
            )
            if rule["action"] == "block":
                raise GuardrailViolationError(f"Output blocked: {rule['reason']}")
            elif rule["action"] == "strip_and_warn":
                sanitized = re.sub(
                    rule["pattern"],
                    "[content removed per safety guidelines]",
                    sanitized,
                    flags=re.IGNORECASE
                )
            elif rule["action"] == "redact":
                sanitized = re.sub(
                    rule["pattern"],
                    "[REDACTED]",
                    sanitized,
                    flags=re.IGNORECASE
                )

    return sanitized
