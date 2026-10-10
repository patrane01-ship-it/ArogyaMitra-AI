"""
ArogyaMitra AI - Subscription Router (Phase 3)
"""
from fastapi import APIRouter, Depends, Header, Request, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

from backend.services.subscription_service import SubscriptionService
from backend.core.dependencies import get_current_user, get_subscription_service
from backend.models.subscription_tier import SubscriptionTier

router = APIRouter(prefix='/api/subscription', tags=['Subscription'])

class OrderRequest(BaseModel):
    tier: str
    amount_paise: int

class VerifyRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str
    tier: str

@router.get("/", response_model=Dict[str, Any])
async def get_current_subscription(
    user=Depends(get_current_user),
    sub_service: SubscriptionService = Depends(get_subscription_service)
):
    sub = await sub_service.get_subscription(user.user_id)
    return sub.to_dict()

@router.post("/order")
async def create_order(
    req: OrderRequest,
    user=Depends(get_current_user),
    sub_service: SubscriptionService = Depends(get_subscription_service)
):
    order = await sub_service.create_order(user.user_id, req.tier, req.amount_paise)
    return {"order": order}

@router.post("/verify")
async def verify_payment(
    req: VerifyRequest,
    user=Depends(get_current_user),
    sub_service: SubscriptionService = Depends(get_subscription_service)
):
    sub = await sub_service.verify_payment_and_upgrade(
        user_id=user.user_id,
        order_id=req.order_id,
        payment_id=req.payment_id,
        signature=req.signature,
        tier=req.tier
    )
    return {"status": "success", "subscription": sub.to_dict()}

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    sub_service: SubscriptionService = Depends(get_subscription_service)
):
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    payload_bytes = await request.body()
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_id = data.get("id", "")
    event_type = data.get("event", "")
    
    try:
        await sub_service.handle_webhook(
            payload_bytes=payload_bytes,
            signature=x_razorpay_signature,
            event_id=event_id,
            event_type=event_type,
            event_data=data
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"status": "ok"}

@router.delete("/")
async def cancel_subscription(
    user=Depends(get_current_user),
    sub_service: SubscriptionService = Depends(get_subscription_service)
):
    await sub_service.cancel_subscription(user.user_id)
    return {"status": "cancelled"}
