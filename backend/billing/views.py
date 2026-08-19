import json
import uuid

from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from core.responses import api_response

from .gateways import payment_gateway
from .models import Invoice, Payment, Plan, Subscription
from .serializers import (
    CreateOrderSerializer,
    EmptyBillingSerializer,
    InvoiceSerializer,
    PaymentSerializer,
    PlanSerializer,
    SubscriptionSerializer,
    VerifyPaymentSerializer,
)
from .services import cancel_subscription, create_order, process_webhook, verify_payment


class PlanListView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PlanSerializer

    def get(self, request):
        return api_response(PlanSerializer(Plan.objects.filter(is_active=True), many=True).data, request=request)


class CreateOrderView(GenericAPIView):
    serializer_class = CreateOrderSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = request.headers.get("Idempotency-Key", "").strip() or str(uuid.uuid4())
        if len(key) > 128:
            raise ValidationError({"idempotency_key": "Idempotency key is too long."})
        result = create_order(
            user=request.user,
            plan_code=serializer.validated_data["plan_code"],
            idempotency_key=key,
            request=request,
        )
        if result.get("free_activated"):
            return api_response({
                "free_activated": True,
                "subscription": SubscriptionSerializer(result["subscription"]).data,
            }, request=request)
        payment = result["payment"]
        return api_response({
            "free_activated": False,
            "key_id": result["key_id"],
            "payment_id": str(payment.id),
            "order_id": payment.provider_order_id,
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "plan": PlanSerializer(payment.plan).data,
            "prefill": {"name": request.user.full_name, "email": request.user.email},
        }, request=request, status=status.HTTP_201_CREATED)


class VerifyPaymentView(GenericAPIView):
    serializer_class = VerifyPaymentSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = verify_payment(user=request.user, request=request, **serializer.validated_data)
        return api_response(SubscriptionSerializer(subscription).data, request=request)


class SubscriptionView(GenericAPIView):
    serializer_class = SubscriptionSerializer
    def get(self, request):
        subscription = Subscription.objects.filter(
            user=request.user,
            status__in=[Subscription.Status.ACTIVE, Subscription.Status.PAST_DUE],
        ).select_related("plan").first()
        if subscription:
            data = SubscriptionSerializer(subscription).data
        else:
            free = Plan.objects.filter(code="free", is_active=True).first()
            data = {
                "id": None,
                "plan": PlanSerializer(free).data if free else None,
                "provider": None,
                "status": "active",
                "started_at": None,
                "current_period_start": None,
                "current_period_end": None,
                "cancel_at_period_end": False,
                "cancelled_at": None,
                "ended_at": None,
            }
        return api_response(data, request=request)


class CancelSubscriptionView(GenericAPIView):
    serializer_class = SubscriptionSerializer
    def post(self, request):
        subscription = cancel_subscription(user=request.user, request=request)
        return api_response(SubscriptionSerializer(subscription).data, request=request)


class PaymentHistoryView(GenericAPIView):
    serializer_class = PaymentSerializer
    def get(self, request):
        items = Payment.objects.filter(user=request.user).select_related("plan")[:100]
        return api_response(PaymentSerializer(items, many=True).data, request=request)


class PaymentCancelView(GenericAPIView):
    serializer_class = PaymentSerializer
    def post(self, request, payment_id):
        payment = Payment.objects.filter(id=payment_id, user=request.user).first()
        if not payment:
            raise NotFound("Payment not found.")
        if payment.status == Payment.Status.CREATED:
            payment.status = Payment.Status.CANCELLED
            payment.save(update_fields=["status", "updated_at"])
        return api_response(PaymentSerializer(payment).data, request=request)


class InvoiceListView(GenericAPIView):
    serializer_class = InvoiceSerializer
    def get(self, request):
        items = Invoice.objects.filter(user=request.user).select_related("subscription__plan")[:100]
        return api_response(InvoiceSerializer(items, many=True).data, request=request)


class RazorpayWebhookView(GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = EmptyBillingSerializer

    def post(self, request):
        raw_body = request.body
        signature = request.headers.get("X-Razorpay-Signature", "")
        event_id = request.headers.get("X-Razorpay-Event-Id", "")
        if not event_id:
            raise ValidationError({"webhook": "Missing Razorpay event ID."})
        if not payment_gateway().verify_webhook_signature(raw_body=raw_body, signature=signature):
            raise ValidationError({"webhook": "Invalid webhook signature."})
        try:
            payload = json.loads(raw_body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValidationError({"webhook": "Invalid JSON payload."}) from exc
        event_type = str(payload.get("event", ""))[:120]
        if not event_type:
            raise ValidationError({"webhook": "Missing event type."})
        event = process_webhook(event_id=event_id, event_type=event_type, payload=payload)
        return api_response({"accepted": True, "status": event.status}, request=request)
