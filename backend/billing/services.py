from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from audit.services import record_audit_event

from .gateways import payment_gateway
from .models import Invoice, Payment, Plan, Subscription, WebhookEvent


def active_plan(code):
    plan = Plan.objects.filter(code=code, is_active=True).first()
    if not plan:
        raise NotFound("Billing plan not found.")
    return plan


@transaction.atomic
def activate_subscription(*, user, plan, payment=None, request=None):
    now = timezone.now()
    Subscription.objects.select_for_update().filter(
        user=user, status__in=[Subscription.Status.ACTIVE, Subscription.Status.PAST_DUE]
    ).update(status=Subscription.Status.EXPIRED, ended_at=now)
    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        payment=payment,
        status=Subscription.Status.ACTIVE,
        started_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=plan.duration_days),
    )
    if payment:
        Invoice.objects.get_or_create(
            payment=payment,
            defaults={
                "invoice_number": f"INV-{now:%Y}-{payment.id.hex[:10].upper()}",
                "user": user,
                "subscription": subscription,
                "amount_minor": payment.amount_minor,
                "currency": payment.currency,
                "issued_at": now,
            },
        )
    record_audit_event(
        action="billing.subscription_activated",
        actor=user,
        target=subscription,
        request=request,
        metadata={"plan": plan.code, "payment_id": str(payment.id) if payment else None},
    )
    return subscription


def create_order(*, user, plan_code, idempotency_key, request=None, gateway=None):
    plan = active_plan(plan_code)
    if plan.amount_minor == 0:
        subscription = activate_subscription(user=user, plan=plan, request=request)
        return {"free_activated": True, "subscription": subscription}
    payment, created = Payment.objects.get_or_create(
        user=user,
        idempotency_key=idempotency_key,
        defaults={"plan": plan, "amount_minor": plan.amount_minor, "currency": plan.currency},
    )
    if not created:
        return {"payment": payment, "key_id": (gateway or payment_gateway()).key_id}
    provider = gateway or payment_gateway()
    try:
        order = provider.create_order(
            amount_minor=payment.amount_minor,
            currency=payment.currency,
            receipt=f"learnos-{payment.id.hex[:24]}",
            notes={"payment_id": str(payment.id), "user_id": str(user.id), "plan": plan.code},
        )
    except Exception:
        payment.status = Payment.Status.FAILED
        payment.failure_code = "order_creation_failed"
        payment.save(update_fields=["status", "failure_code", "updated_at"])
        raise
    payment.provider_order_id = order["id"]
    payment.provider_payload = {"order_status": order.get("status", "created")}
    payment.save(update_fields=["provider_order_id", "provider_payload", "updated_at"])
    record_audit_event(action="billing.order_created", actor=user, target=payment, request=request, metadata={"plan": plan.code, "amount_minor": plan.amount_minor})
    return {"payment": payment, "key_id": provider.key_id}


@transaction.atomic
def verify_payment(*, user, payment_id, razorpay_payment_id, razorpay_order_id, razorpay_signature, request=None, gateway=None):
    payment = Payment.objects.select_for_update().filter(id=payment_id, user=user).select_related("plan").first()
    if not payment:
        raise NotFound("Payment not found.")
    if payment.status == Payment.Status.CAPTURED:
        return payment.subscription
    if not payment.provider_order_id or payment.provider_order_id != razorpay_order_id:
        raise ValidationError({"razorpay_order_id": "Order does not match the server-created order."})
    provider = gateway or payment_gateway()
    if not provider.verify_payment_signature(order_id=payment.provider_order_id, payment_id=razorpay_payment_id, signature=razorpay_signature):
        record_audit_event(action="billing.signature_rejected", actor=user, target=payment, request=request)
        raise ValidationError({"razorpay_signature": "Payment signature verification failed."})
    provider_payment = provider.fetch_payment(razorpay_payment_id)
    if provider_payment.get("order_id") != payment.provider_order_id or provider_payment.get("amount") != payment.amount_minor or provider_payment.get("currency") != payment.currency:
        raise ValidationError({"payment": "Provider payment details do not match this order."})
    if provider_payment.get("status") not in {"captured", "authorized"}:
        raise ValidationError({"payment": "Payment has not been authorized or captured."})
    payment.provider_payment_id = razorpay_payment_id
    payment.signature_verified = True
    payment.status = Payment.Status.CAPTURED if provider_payment["status"] == "captured" else Payment.Status.AUTHORIZED
    payment.provider_payload = {"method": provider_payment.get("method"), "status": provider_payment.get("status")}
    payment.paid_at = timezone.now()
    payment.save()
    if payment.status != Payment.Status.CAPTURED:
        raise ValidationError({"payment": "Payment is authorized and awaiting capture."})
    return activate_subscription(user=user, plan=payment.plan, payment=payment, request=request)


@transaction.atomic
def cancel_subscription(*, user, request=None, gateway=None):
    subscription = Subscription.objects.select_for_update().filter(user=user, status__in=[Subscription.Status.ACTIVE, Subscription.Status.PAST_DUE]).select_related("plan").first()
    if not subscription:
        raise NotFound("No active subscription found.")
    if subscription.provider_subscription_id:
        (gateway or payment_gateway()).cancel_subscription(subscription.provider_subscription_id)
    subscription.cancel_at_period_end = True
    subscription.cancelled_at = timezone.now()
    subscription.save(update_fields=["cancel_at_period_end", "cancelled_at", "updated_at"])
    record_audit_event(action="billing.subscription_cancelled", actor=user, target=subscription, request=request)
    return subscription


def entity(payload, name):
    return payload.get("payload", {}).get(name, {}).get("entity", {})


@transaction.atomic
def process_webhook(*, event_id, event_type, payload):
    event, created = WebhookEvent.objects.get_or_create(
        event_id=event_id,
        defaults={"event_type": event_type, "payload": payload},
    )
    if not created:
        return event
    now = timezone.now()
    payment_data = entity(payload, "payment")
    refund_data = entity(payload, "refund")
    provider_payment_id = payment_data.get("id", "")
    order_id = payment_data.get("order_id") or entity(payload, "order").get("id")
    payment = Payment.objects.select_for_update().filter(provider_order_id=order_id).first() if order_id else None
    if not payment and refund_data.get("payment_id"):
        payment = Payment.objects.select_for_update().filter(
            provider_payment_id=refund_data["payment_id"]
        ).first()
    try:
        if payment and event_type in {"payment.captured", "order.paid"}:
            payment.provider_payment_id = provider_payment_id or payment.provider_payment_id
            payment.status = Payment.Status.CAPTURED
            payment.signature_verified = True
            payment.paid_at = payment.paid_at or now
            payment.save()
            if not hasattr(payment, "subscription"):
                activate_subscription(user=payment.user, plan=payment.plan, payment=payment)
        elif payment and event_type == "payment.failed":
            payment.status = Payment.Status.FAILED
            payment.failure_code = payment_data.get("error_code", "payment_failed") or "payment_failed"
            payment.failure_description = payment_data.get("error_description", "") or ""
            payment.save()
        elif payment and event_type in {"refund.created", "refund.processed", "refund.failed"}:
            if event_type == "refund.processed":
                payment.status = Payment.Status.REFUNDED
                payment.refunded_at = now
                payment.save()
                Invoice.objects.filter(payment=payment).update(status=Invoice.Status.REFUNDED, refunded_at=now)
                Subscription.objects.filter(payment=payment, status=Subscription.Status.ACTIVE).update(status=Subscription.Status.CANCELLED, ended_at=now)
            elif event_type == "refund.created":
                payment.status = Payment.Status.REFUND_PENDING
                payment.save(update_fields=["status", "updated_at"])
            else:
                payment.failure_code = "refund_failed"
                payment.failure_description = refund_data.get("error_description", "") or "Refund processing failed."
                payment.save(update_fields=["failure_code", "failure_description", "updated_at"])
        else:
            subscription_data = entity(payload, "subscription")
            provider_id = subscription_data.get("id")
            subscription = Subscription.objects.filter(provider_subscription_id=provider_id).first() if provider_id else None
            if subscription and event_type.startswith("subscription."):
                status_map = {"subscription.activated": Subscription.Status.ACTIVE, "subscription.pending": Subscription.Status.PAST_DUE, "subscription.cancelled": Subscription.Status.CANCELLED, "subscription.completed": Subscription.Status.EXPIRED, "subscription.halted": Subscription.Status.PAST_DUE}
                if event_type in status_map:
                    subscription.status = status_map[event_type]
                    subscription.save(update_fields=["status", "updated_at"])
            else:
                event.status = WebhookEvent.Status.IGNORED
        if event.status != WebhookEvent.Status.IGNORED:
            event.status = WebhookEvent.Status.PROCESSED
        event.processed_at = now
        event.save()
    except Exception as exc:
        event.status = WebhookEvent.Status.FAILED
        event.error_message = str(exc)[:500]
        event.save()
        raise
    return event
