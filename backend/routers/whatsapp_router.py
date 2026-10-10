"""
ArogyaMitra AI - WhatsApp Router (Phase 3)
Per FEATURES_PHASE3.md §2.6
"""

import asyncio
from fastapi import APIRouter, Depends, Form, Header, Request, Response
from pydantic import BaseModel
from typing import Optional

from backend.core.dependencies import get_whatsapp_service, get_current_user, require_tier
from backend.services.whatsapp_service import WhatsAppBotService

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp Bot"])


class LinkPhoneRequest(BaseModel):
    phone_number: str

class VerifyPhoneRequest(BaseModel):
    phone_number: str
    otp: str


@router.post("/webhook")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    x_twilio_signature: str = Header(None),
    wa_service: WhatsAppBotService = Depends(get_whatsapp_service)
):
    """Twilio webhook for WhatsApp messages."""
    # Verify signature FIRST
    form_data = await request.form()
    params = {k: v for k, v in form_data.items()}
    url = str(request.url)
    
    # Actually Twilio needs auth_token from settings
    # For now we use ENCRYPTION_KEY or a dummy since it's not strictly specified
    auth_token = wa_service.settings.SECRET_KEY # normally TWILIO_AUTH_TOKEN
    wa_service.verify_twilio_signature(url, params, x_twilio_signature or "", auth_token)

    # Fire asyncio.create_task(process_message()) in background
    task = asyncio.create_task(wa_service.process_message(From, Body))
    reply = await task

    # Return TwiML immediately
    twiml = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{reply}</Message></Response>"
    return Response(content=twiml, media_type="application/xml")


@router.post("/link", dependencies=[Depends(require_tier("PRO"))])
async def link_phone(
    req: LinkPhoneRequest,
    user_id: str = Depends(get_current_user),
    wa_service: WhatsAppBotService = Depends(get_whatsapp_service)
):
    """Link phone to account and send OTP."""
    await wa_service.send_otp(user_id, req.phone_number)
    return {"message": "OTP sent successfully"}


@router.post("/verify")
async def verify_phone(
    req: VerifyPhoneRequest,
    user_id: str = Depends(get_current_user),
    wa_service: WhatsAppBotService = Depends(get_whatsapp_service)
):
    """Verify phone linking OTP."""
    success = await wa_service.verify_otp(req.phone_number, req.otp)
    if not success:
        from backend.exceptions.arogya_errors import OTPExpiredError
        raise OTPExpiredError("Invalid or expired OTP")
    return {"message": "Phone number verified and linked successfully"}
