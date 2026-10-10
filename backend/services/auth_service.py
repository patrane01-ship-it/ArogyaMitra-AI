"""
ArogyaMitra AI - Auth Service
JWT token creation/validation, password hashing, and token rotation.
Per FEATURES_PHASE2.md §2.1 and TECH_STACK_PHASE2.md §3.
"""

import re
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from backend.config import settings
from backend.core.logger import logger
from backend.exceptions.arogya_errors import (
    WeakPasswordError,
    InvalidTokenError,
    TokenExpiredError,
)

# ── Password hashing ──────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Token constants ───────────────────────────────────────────
ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# Password strength: min 8 chars, 1 uppercase, 1 digit
_PASSWORD_REGEX = re.compile(r"^(?=.*[A-Z])(?=.*\d).{8,}$")


class AuthService:
    """Stateless JWT auth service. All methods are class-level (no instance state)."""

    # ── Password helpers ───────────────────────────────────────

    @staticmethod
    def validate_password_strength(password: str) -> None:
        """Raise WeakPasswordError if password doesn't meet policy."""
        if not password or not _PASSWORD_REGEX.match(password):
            raise WeakPasswordError(
                "Password must be at least 8 characters with at least 1 uppercase letter and 1 number"
            )

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Hash a plain-text password with bcrypt."""
        return pwd_context.hash(plain_password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify plain password against bcrypt hash."""
        return pwd_context.verify(plain_password, hashed_password)

    # ── Token creation ─────────────────────────────────────────

    @staticmethod
    def create_access_token(user_id: str, email: str) -> str:
        """
        Create a short-lived JWT access token.
        Payload includes: sub (user_id), email, type, jti, iat, exp.
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "email": email,
            "type": ACCESS_TOKEN_TYPE,
            "jti": str(uuid.uuid4()),  # unique token ID (for future revocation)
            "iat": now,
            "exp": expire,
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"[Auth] Access token created for user_id={user_id}")
        return token

    @staticmethod
    def create_refresh_token() -> Tuple[str, str]:
        """
        Create an opaque refresh token (URL-safe random bytes).
        Returns (raw_token, hashed_token).
        The raw token is sent to the client; only the hash is stored in DB.
        """
        raw = secrets.token_urlsafe(64)
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        return raw, hashed

    @staticmethod
    def hash_refresh_token(raw_token: str) -> str:
        """Hash a raw refresh token for secure DB storage."""
        return hashlib.sha256(raw_token.encode()).hexdigest()

    # ── Token validation ────────────────────────────────────────

    @staticmethod
    def decode_access_token(token: str) -> dict:
        """
        Decode and validate a JWT access token.
        Raises TokenExpiredError or InvalidTokenError on failure.
        Returns the full payload dict on success.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != ACCESS_TOKEN_TYPE:
                raise InvalidTokenError("Token type mismatch")
            return payload
        except ExpiredSignatureError:
            raise TokenExpiredError()
        except JWTError as e:
            logger.warning(f"[Auth] JWT decode error: {e}")
            raise InvalidTokenError("Token signature verification failed")

    @staticmethod
    def extract_user_id(token: str) -> str:
        """Extract user_id (sub) from a valid access token."""
        payload = AuthService.decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Token missing subject claim")
        return user_id
