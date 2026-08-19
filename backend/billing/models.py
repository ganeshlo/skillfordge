from django.conf import settings
from django.db import models

from core.models import TimestampedModel


class Plan(TimestampedModel):
    class Interval(models.TextChoices):
        MONTH = "month", "Monthly"
        YEAR = "year", "Yearly"

    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=240, blank=True)
    amount_minor = models.PositiveIntegerField()
    compare_at_amount_minor = models.PositiveIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="INR")
    billing_interval = models.CharField(max_length=10, choices=Interval.choices, default=Interval.MONTH)
    duration_days = models.PositiveSmallIntegerField(default=30)
    features = models.JSONField(default=list)
    limits = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "amount_minor"]


class Payment(TimestampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        AUTHORIZED = "authorized", "Authorized"
        CAPTURED = "captured", "Captured"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUND_PENDING = "refund_pending", "Refund pending"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="payments", on_delete=models.PROTECT)
    plan = models.ForeignKey(Plan, related_name="payments", on_delete=models.PROTECT)
    provider = models.CharField(max_length=30, default="razorpay")
    provider_order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    provider_payment_id = models.CharField(max_length=100, blank=True, db_index=True)
    amount_minor = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.CREATED, db_index=True)
    idempotency_key = models.CharField(max_length=128)
    signature_verified = models.BooleanField(default=False)
    failure_code = models.CharField(max_length=120, blank=True)
    failure_description = models.CharField(max_length=500, blank=True)
    provider_payload = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "idempotency_key"], name="unique_user_payment_idempotency")
        ]
        indexes = [models.Index(fields=["user", "-created_at"])]


class Subscription(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past due"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="subscriptions", on_delete=models.PROTECT)
    plan = models.ForeignKey(Plan, related_name="subscriptions", on_delete=models.PROTECT)
    payment = models.OneToOneField(Payment, related_name="subscription", null=True, blank=True, on_delete=models.SET_NULL)
    provider = models.CharField(max_length=30, default="razorpay")
    provider_subscription_id = models.CharField(max_length=100, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    started_at = models.DateTimeField()
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status", "-created_at"])]


class Invoice(TimestampedModel):
    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"
        VOID = "void", "Void"

    invoice_number = models.CharField(max_length=40, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="invoices", on_delete=models.PROTECT)
    payment = models.OneToOneField(Payment, related_name="invoice", on_delete=models.PROTECT)
    subscription = models.ForeignKey(Subscription, related_name="invoices", on_delete=models.PROTECT)
    amount_minor = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PAID)
    issued_at = models.DateTimeField()
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-issued_at"]


class WebhookEvent(TimestampedModel):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSED = "processed", "Processed"
        IGNORED = "ignored", "Ignored"
        FAILED = "failed", "Failed"

    provider = models.CharField(max_length=30, default="razorpay")
    event_id = models.CharField(max_length=160, unique=True)
    event_type = models.CharField(max_length=120, db_index=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    error_message = models.CharField(max_length=500, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
