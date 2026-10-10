"""
ArogyaMitra AI - WhatsApp Bot Service (Phase 3)
Per FEATURES_PHASE3.md §2.6
"""

import hmac
import hashlib
import base64
import secrets
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from groq import AsyncGroq
from passlib.context import CryptContext

from backend.repositories.whatsapp_repo import WhatsAppRepository
from backend.repositories.risk_score_repo import RiskScoreRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.core.cache import ArogyaCache
from backend.config import Settings
from backend.core.sanitizer import sanitize_string
from backend.core.guardrails import apply_output_guardrails
from backend.exceptions.arogya_errors import (
    InvalidWebhookSignatureError,
    BotRateLimitError,
    OTPExpiredError,
)
from backend.core.logger import logger

_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class WhatsAppBotService:
    def __init__(
        self,
        wa_repo: WhatsAppRepository,
        risk_repo: RiskScoreRepository,
        param_repo: ClinicalParameterRepository,
        cache: ArogyaCache,
        settings: Settings,
    ):
        self.wa_repo = wa_repo
        self.risk_repo = risk_repo
        self.param_repo = param_repo
        self.cache = cache
        self.settings = settings
        self.groq = AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

    def verify_twilio_signature(self, url: str, params: Dict[str, str], signature: str, auth_token: str) -> bool:
        """Verify Twilio webhook signature using HMAC-SHA1."""
        sorted_keys = sorted(params.keys())
        data_string = url + "".join(f"{k}{params[k]}" for k in sorted_keys)
        mac = hmac.new(auth_token.encode("utf-8"), data_string.encode("utf-8"), hashlib.sha1)
        expected_sig = base64.b64encode(mac.digest()).decode("utf-8")
        if not hmac.compare_digest(expected_sig, signature):
            raise InvalidWebhookSignatureError("Webhook signature verification failed")
        return True

    async def process_message(self, phone_number: str, message_body: str, user_id: Optional[str] = None) -> str:
        """Process an incoming WhatsApp message."""
        rate_key = f"whatsapp_rate:{phone_number}"
        requests = await self.cache.increment(rate_key)
        if requests == 1:
            await self.cache.expire(rate_key, 3600)
        if requests > 20:
            raise BotRateLimitError("Too many messages. Please wait before sending again.")

        sanitized_input = sanitize_string(message_body)
        phone_hash = hashlib.sha256(phone_number.encode("utf-8")).hexdigest()

        intent = "UNKNOWN"
        if self.groq:
            try:
                response = await self.groq.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an intent classifier. Return ONLY one of: GET_RISK_SCORE, GET_LATEST_PARAMS, HELP, UNKNOWN. No other text."
                        },
                        {
                            "role": "user",
                            "content": sanitized_input
                        }
                    ],
                    temperature=0.0,
                    max_tokens=10,
                )
                predicted_intent = response.choices[0].message.content.strip().upper()
                if predicted_intent in ["GET_RISK_SCORE", "GET_LATEST_PARAMS", "HELP", "UNKNOWN"]:
                    intent = predicted_intent
            except Exception as e:
                logger.error(f"Intent classification failed: {e}")
        
        logger.info(f"[WhatsApp] Processed message | phone_hash={phone_hash} | intent={intent}")

        reply = ""
        session = await self.wa_repo.get_by_phone(phone_number)
        active_profile_id = session.active_profile_id if session and session.active_profile_id else None

        if intent == "HELP":
            reply = "Hi! I am ArogyaMitra. I can help you with your health data.\nSend me messages like:\n- 'What is my latest risk score?'\n- 'Show me my latest parameters.'"
        elif intent == "GET_RISK_SCORE":
            if not session or not session.is_verified() or not active_profile_id:
                reply = "Please link your phone number and verify it to access your risk score."
            else:
                try:
                    score_obj = await self.risk_repo.get_latest_score(active_profile_id)
                    if score_obj:
                        reply = f"Your latest health risk score is {score_obj.score}. (Calculated at {score_obj.calculated_at.strftime('%Y-%m-%d')})"
                    else:
                        reply = "You don't have any computed risk scores yet."
                except Exception:
                    reply = "I couldn't retrieve your risk score right now."
        elif intent == "GET_LATEST_PARAMS":
            if not session or not session.is_verified() or not active_profile_id:
                reply = "Please link your phone number and verify it to access your parameters."
            else:
                try:
                    params = await self.param_repo.get_by_profile(active_profile_id)
                    if params:
                        # take the 5 most recent
                        latest = sorted(params, key=lambda x: x.recorded_at, reverse=True)[:5]
                        reply_lines = ["Your latest clinical parameters:"]
                        for p in latest:
                            reply_lines.append(f"- {p.parameter_name}: {p.value} {p.unit}")
                        reply = "\n".join(reply_lines)
                    else:
                        reply = "You don't have any clinical parameters recorded yet."
                except Exception:
                    reply = "I couldn't retrieve your parameters right now."
        else:
            reply = "I'm sorry, I didn't understand that. Type 'HELP' to see what I can do."

        reply = apply_output_guardrails(reply)
        return reply

    async def send_otp(self, user_id: str, phone_number: str) -> None:
        """Send OTP to link phone number."""
        otp_val = secrets.randbelow(1000000)
        otp_str = f"{otp_val:06d}"
        
        session = await self.wa_repo.get_or_create(user_id, phone_number)
        session.otp_hash = _pwd_context.hash(otp_str)
        session.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        await self.wa_repo.update(session)

        attempts_key = f"otp_attempts:{phone_number}"
        await self.cache.delete(attempts_key)

        if self.settings.ENVIRONMENT == "development" or self.settings.DEBUG:
            logger.info(f"DEVELOPMENT MODE | OTP for {phone_number} is {otp_str}")
        else:
            # Integration with Twilio for sending OTP goes here
            pass

    async def verify_otp(self, phone_number: str, otp_plain: str) -> bool:
        """Verify OTP for phone number."""
        attempts_key = f"otp_attempts:{phone_number}"
        attempts = await self.cache.increment(attempts_key)
        if attempts == 1:
            await self.cache.expire(attempts_key, 600)
        
        if attempts > 3:
            raise BotRateLimitError("Maximum OTP verification attempts exceeded.")

        session = await self.wa_repo.get_by_phone(phone_number)
        if not session:
            return False

        if session.is_otp_valid(otp_plain):
            session.otp_hash = None
            session.otp_expires_at = None
            session.verified_at = datetime.now(timezone.utc)
            await self.wa_repo.update(session)
            await self.cache.delete(attempts_key)
            return True

        return False
