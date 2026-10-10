"""
ArogyaMitra AI - Secure Share Service
Generates and verifies time-limited, signed JWT share tokens for doctor consultation views.
Per FEATURES.md §3 (Feature 6) and PRODUCTION_BACKEND.md §10.6, §10.7.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import jwt, JWTError, ExpiredSignatureError
from backend.config import settings
from backend.core.logger import logger
from backend.exceptions.arogya_errors import ShareTokenExpiredError, InvalidShareTokenError, ArogyaError


class ShareService:
    """Service for issuing and verifying secure share tokens."""

    ALGORITHM = "HS256"

    @classmethod
    def generate_token(
        cls,
        resource_id: str,
        resource_type: str,
        user_id: str,
        expiry_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Generate a signed, expiring JWT token for a specific record or report.
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=expiry_hours)

        payload = {
            "sub": resource_id,
            "type": "share",
            "resource_type": resource_type,
            "user_id": user_id,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        try:
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm=cls.ALGORITHM)
            logger.info(
                f"[ShareService] Token created | resource={resource_type}:{resource_id} | exp={expires_at.isoformat()}"
            )
            return {
                "token": token,
                "share_url": f"/share/{token}",
                "expires_at": expires_at,
            }
        except Exception as e:
            logger.error(f"[ShareService] Error generating share token: {e}")
            raise ArogyaError("Could not generate share token", status_code=500)

    @classmethod
    def verify_token(cls, token: str) -> Dict[str, Any]:
        """
        Verify a share token. Returns payload on success.
        Raises ShareTokenExpiredError (410) if expired.
        Raises InvalidShareTokenError (401/400) if invalid or tampered.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[cls.ALGORITHM])
            if payload.get("type") != "share":
                raise InvalidShareTokenError("Token is not a valid share token")
            return payload
        except ExpiredSignatureError:
            logger.warning("[ShareService] Expired share token accessed")
            raise ShareTokenExpiredError("Share link has expired")
        except JWTError as e:
            logger.warning(f"[ShareService] Invalid share token: {e}")
            raise InvalidShareTokenError("Invalid or corrupted share link")
