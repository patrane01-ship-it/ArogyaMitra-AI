"""
ArogyaMitra AI - Prompt Guard
Detects and neutralizes prompt injection attempts in user inputs and document contents.
Per PRODUCTION_BACKEND.md §7.2.
"""

import re
from backend.core.logger import logger
from backend.exceptions.arogya_errors import PromptInjectionDetectedError

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"forget\s+(everything|all|what)",
    r"you\s+are\s+now\s+(a|an)",
    r"act\s+as\s+(a|an|if)",
    r"pretend\s+(to\s+be|you('re| are))",
    r"disregard\s+(the|all|your)",
    r"new\s+instructions?:",
    r"system\s*:\s*",
    r"\[INST\]",
    r"<\|im_start\|>",
    r"###\s*instruction",
    r"override\s+(safety|guardrail)",
]


def detect_injection(text: str) -> bool:
    """Check if text contains prompt injection patterns."""
    if not text:
        return False
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def sanitize_for_prompt(text: str, max_chars: int = 3000) -> str:
    """
    Sanitize text before inserting into any LLM prompt:
    1. Detect injection patterns -> raise PromptInjectionDetectedError
    2. Truncate to max_chars
    3. Remove non-printable control characters
    4. Escape curly braces to prevent f-string / template injection
    """
    if not text:
        return ""

    if detect_injection(text):
        logger.warning(f"[PromptGuard] INJECTION_DETECTED | length={len(text)}")
        raise PromptInjectionDetectedError(
            "Document contains content that cannot be processed"
        )

    # Truncate
    text = text[:max_chars]

    # Remove unprintable chars (keep standard whitespace)
    text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\r\t")

    # Escape curly braces
    text = text.replace("{", "{{").replace("}", "}}")

    return text
