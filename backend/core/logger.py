"""
ArogyaMitra AI - Logger Configuration
Standard logging module (fallback when loguru unavailable due to disk space).
"""

import logging
import sys
import os
from backend.config import settings

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Create logger
logger = logging.getLogger("arogya")
logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

# Console handler
if settings.DEBUG:
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

# File handler - all levels
file_handler = logging.FileHandler("logs/arogya.log")
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

# Error-only file handler
error_handler = logging.FileHandler("logs/arogya_errors.log")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(file_format)
logger.addHandler(error_handler)

__all__ = ["logger"]
