from rest_framework import serializers

from .models import Invoice, Payment, Plan, Subscription


class EmptyBillingSerializer(serializers.Serializer):
    pass


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "code", "name", "description", "amount_minor", "compare_at_amount_minor", "currency", "billing_interval", "duration_days", "features", "limits", "is_featured"]


class PaymentSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "plan", "provider", "provider_order_id", "provider_payment_id", "amount_minor", "currency", "status", "signature_verified", "failure_code", "failure_description", "paid_at", "refunded_at", "created_at", "updated_at"]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "plan", "provider", "status", "started_at", "current_period_start", "current_period_end", "cancel_at_period_end", "cancelled_at", "ended_at", "created_at", "updated_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="subscription.plan.name", read_only=True)

    class Meta:
        model = Invoice
        fields = ["id", "invoice_number", "plan_name", "amount_minor", "currency", "status", "issued_at", "refunded_at"]


class CreateOrderSerializer(serializers.Serializer):
    plan_code = serializers.SlugField(max_length=40)


class VerifyPaymentSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    razorpay_payment_id = serializers.CharField(max_length=100)
    razorpay_order_id = serializers.CharField(max_length=100)
    razorpay_signature = serializers.CharField(max_length=256)
