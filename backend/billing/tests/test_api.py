import hashlib
import hmac
import json
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User, UserPreference, UserProfile
from billing.models import Invoice, Payment, Plan, Subscription, WebhookEvent
from billing.services import activate_subscription


class FakeGateway:
    key_id = "rzp_test_public"

    def create_order(self, *, amount_minor, currency, receipt, notes):
        return {"id": "order_server_created", "amount": amount_minor, "currency": currency, "status": "created"}

    def verify_payment_signature(self, **kwargs):
        return kwargs["signature"] == "valid-signature"

    def fetch_payment(self, payment_id):
        return {"id": payment_id, "order_id": "order_server_created", "amount": 100, "currency": "INR", "status": "captured", "method": "upi"}

    def cancel_subscription(self, subscription_id):
        return {"id": subscription_id, "status": "cancelled"}


def make_user(email):
    user = User.objects.create_user(email, "A-strong-test-password-482!", full_name="Billing User")
    UserProfile.objects.create(user=user)
    UserPreference.objects.create(user=user)
    return user


class BillingAPITests(APITestCase):
    def setUp(self):
        self.user = make_user("billing@example.com")
        self.other = make_user("other-billing@example.com")
        self.free, _ = Plan.objects.update_or_create(code="free", defaults={"name": "Free", "amount_minor": 0, "duration_days": 32700})
        self.pro, _ = Plan.objects.update_or_create(code="pro", defaults={"name": "Pro", "amount_minor": 100, "compare_at_amount_minor": 99900, "duration_days": 30})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(self.user)}")

    @patch("billing.services.payment_gateway", return_value=FakeGateway())
    def test_order_uses_server_plan_price_and_is_idempotent(self, _gateway):
        url = reverse("billing-create-order")
        first = self.client.post(url, {"plan_code": "pro", "amount_minor": 1}, format="json", HTTP_IDEMPOTENCY_KEY="same-key")
        second = self.client.post(url, {"plan_code": "pro"}, format="json", HTTP_IDEMPOTENCY_KEY="same-key")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.data["data"]["amount_minor"], 100)
        self.assertEqual(first.data["data"]["payment_id"], second.data["data"]["payment_id"])
        self.assertEqual(Payment.objects.count(), 1)

    @patch("billing.services.payment_gateway", return_value=FakeGateway())
    def test_signature_is_required_before_subscription_and_invoice(self, _gateway):
        created = self.client.post(reverse("billing-create-order"), {"plan_code": "pro"}, format="json")
        payment_id = created.data["data"]["payment_id"]
        payload = {"payment_id": payment_id, "razorpay_payment_id": "pay_123", "razorpay_order_id": "order_server_created", "razorpay_signature": "invalid"}
        rejected = self.client.post(reverse("billing-verify-payment"), payload, format="json")
        self.assertEqual(rejected.status_code, 400)
        self.assertFalse(Subscription.objects.exists())

        payload["razorpay_signature"] = "valid-signature"
        verified = self.client.post(reverse("billing-verify-payment"), payload, format="json")
        self.assertEqual(verified.status_code, 200)
        self.assertEqual(verified.data["data"]["plan"]["code"], "pro")
        self.assertTrue(Invoice.objects.filter(user=self.user).exists())

    def test_free_plan_activates_without_collecting_payment(self):
        response = self.client.post(reverse("billing-create-order"), {"plan_code": "free"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["free_activated"])
        self.assertFalse(Payment.objects.exists())

    def test_billing_history_is_user_scoped(self):
        Payment.objects.create(user=self.other, plan=self.pro, amount_minor=100, currency="INR", idempotency_key="other")
        response = self.client.get(reverse("billing-payment-history"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])

    @override_settings(RAZORPAY_WEBHOOK_SECRET="webhook-secret")
    def test_webhook_signature_and_event_id_are_verified_and_idempotent(self):
        payment = Payment.objects.create(user=self.user, plan=self.pro, amount_minor=100, currency="INR", idempotency_key="webhook", provider_order_id="order_webhook")
        payload = {"event": "payment.captured", "payload": {"payment": {"entity": {"id": "pay_webhook", "order_id": "order_webhook"}}}}
        raw = json.dumps(payload, separators=(",", ":")).encode()
        signature = hmac.new(b"webhook-secret", raw, hashlib.sha256).hexdigest()
        headers = {"HTTP_X_RAZORPAY_SIGNATURE": signature, "HTTP_X_RAZORPAY_EVENT_ID": "event-1"}
        first = self.client.generic("POST", reverse("billing-razorpay-webhook"), raw, content_type="application/json", **headers)
        second = self.client.generic("POST", reverse("billing-razorpay-webhook"), raw, content_type="application/json", **headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.CAPTURED)
        self.assertEqual(WebhookEvent.objects.count(), 1)
        self.assertEqual(Subscription.objects.filter(user=self.user).count(), 1)

        invalid = self.client.generic("POST", reverse("billing-razorpay-webhook"), raw, content_type="application/json", HTTP_X_RAZORPAY_SIGNATURE="bad", HTTP_X_RAZORPAY_EVENT_ID="event-2")
        self.assertEqual(invalid.status_code, 400)

    @patch("billing.services.payment_gateway", return_value=FakeGateway())
    def test_user_can_cancel_active_paid_subscription_at_period_end(self, _gateway):
        payment = Payment.objects.create(user=self.user, plan=self.pro, amount_minor=100, currency="INR", idempotency_key="cancel", status=Payment.Status.CAPTURED)
        subscription = activate_subscription(user=self.user, plan=self.pro, payment=payment)
        response = self.client.post(reverse("billing-subscription-cancel"))
        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db()
        self.assertTrue(subscription.cancel_at_period_end)

    @override_settings(RAZORPAY_WEBHOOK_SECRET="webhook-secret")
    def test_failure_and_refund_webhooks_update_payment_invoice_and_subscription(self):
        failed = Payment.objects.create(user=self.user, plan=self.pro, amount_minor=100, currency="INR", idempotency_key="failed", provider_order_id="order_failed")
        self._webhook("failed-event", {"event": "payment.failed", "payload": {"payment": {"entity": {"id": "pay_failed", "order_id": "order_failed", "error_code": "BAD_REQUEST_ERROR", "error_description": "Bank declined"}}}})
        failed.refresh_from_db()
        self.assertEqual(failed.status, Payment.Status.FAILED)

        paid = Payment.objects.create(user=self.user, plan=self.pro, amount_minor=100, currency="INR", idempotency_key="refund", provider_order_id="order_refund", provider_payment_id="pay_refund", status=Payment.Status.CAPTURED)
        subscription = activate_subscription(user=self.user, plan=self.pro, payment=paid)
        response = self._webhook("refund-event", {"event": "refund.processed", "payload": {"refund": {"entity": {"id": "rfnd_1", "payment_id": "pay_refund"}}}})
        self.assertEqual(response.status_code, 200)
        paid.refresh_from_db()
        subscription.refresh_from_db()
        self.assertEqual(paid.status, Payment.Status.REFUNDED)
        self.assertEqual(subscription.status, Subscription.Status.CANCELLED)
        self.assertEqual(Invoice.objects.get(payment=paid).status, Invoice.Status.REFUNDED)

    def _webhook(self, event_id, payload):
        raw = json.dumps(payload, separators=(",", ":")).encode()
        signature = hmac.new(b"webhook-secret", raw, hashlib.sha256).hexdigest()
        return self.client.generic("POST", reverse("billing-razorpay-webhook"), raw, content_type="application/json", HTTP_X_RAZORPAY_SIGNATURE=signature, HTTP_X_RAZORPAY_EVENT_ID=event_id)
