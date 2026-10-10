"""
ArogyaMitra AI - Input Sanitizer
Sanitizes user input before database storage, LLM prompt generation, and file operations.
Per PRODUCTION_BACKEND.md §3.4.
"""

import re
import unicodedata


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize general string inputs:
    1. Strip leading/trailing whitespace
    2. Normalize unicode (NFC)
    3. Remove null bytes
    4. Truncate to max_length
    """
    if not isinstance(value, str):
        return ""
    
    val = value.strip()
    val = unicodedata.normalize("NFC", val)
    val = val.replace("\x00", "")
    return val[:max_length]


def sanitize_filename(name: str) -> str:
    """
    Sanitize filename to prevent directory traversal and unsafe filenames:
    1. Replace all non-alphanumeric except . _ - with _
    2. Strip leading dots
    3. Truncate to 100 chars
    """
    if not isinstance(name, str):
        return "unnamed_file"
    
    clean = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    clean = clean.lstrip(".")
    if not clean:
        clean = "unnamed_file"
    return clean[:100]
