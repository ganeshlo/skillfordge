import hashlib
import hmac

import httpx
from django.conf import settings
from rest_framework.exceptions import APIException


class PaymentProviderError(APIException):
    status_code = 502
    default_detail = "The payment provider is temporarily unavailable."
    default_code = "payment_provider_error"


class RazorpayGateway:
    name = "razorpay"

    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.base_url = settings.RAZORPAY_API_URL

    @property
    def enabled(self):
        return bool(self.key_id and self.key_secret)

    def _request(self, method, path, **kwargs):
        if not self.enabled:
            raise PaymentProviderError("Razorpay is not configured. Add test or live API credentials.")
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                auth=(self.key_id, self.key_secret),
                timeout=settings.RAZORPAY_TIMEOUT_SECONDS,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PaymentProviderError() from exc

    def create_order(self, *, amount_minor, currency, receipt, notes):
        return self._request("POST", "/orders", json={
            "amount": amount_minor,
            "currency": currency,
            "receipt": receipt[:40],
            "notes": notes,
        })

    def fetch_payment(self, payment_id):
        return self._request("GET", f"/payments/{payment_id}")

    def cancel_subscription(self, subscription_id):
        return self._request("POST", f"/subscriptions/{subscription_id}/cancel", json={"cancel_at_cycle_end": 1})

    def verify_payment_signature(self, *, order_id, payment_id, signature):
        expected = hmac.new(
            self.key_secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(self, *, raw_body, signature):
        expected = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
        ).hexdigest()
        return bool(settings.RAZORPAY_WEBHOOK_SECRET) and hmac.compare_digest(expected, signature)


def payment_gateway():
    return RazorpayGateway()
