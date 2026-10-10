"""
ArogyaMitra AI - Razorpay Adapter (Phase 3)
"""
import uuid
import hmac
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any

class RazorpayAdapter(ABC):
    @abstractmethod
    async def create_order(self, amount_paise: int, currency: str = "INR", receipt: str = "") -> Dict[str, Any]:
        pass

    @abstractmethod
    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str, secret: str) -> bool:
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload_bytes: bytes, signature: str, secret: str) -> bool:
        pass

class MockRazorpayAdapter(RazorpayAdapter):
    """
    Mock Razorpay Adapter for local dev and testing.
    Uses real HMAC-SHA256 verification (never skips it).
    """
    async def create_order(self, amount_paise: int, currency: str = "INR", receipt: str = "") -> Dict[str, Any]:
        return {
            "id": f"order_{uuid.uuid4().hex[:14]}",
            "entity": "order",
            "amount": amount_paise,
            "amount_paid": 0,
            "amount_due": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "attempts": 0,
            "created_at": 1600000000
        }

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str, secret: str) -> bool:
        msg = f"{order_id}|{payment_id}"
        expected_sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    def verify_webhook_signature(self, payload_bytes: bytes, signature: str, secret: str) -> bool:
        expected_sig = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    @staticmethod
    def generate_test_signature(order_id: str, payment_id: str, secret: str) -> str:
        msg = f"{order_id}|{payment_id}"
        return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
