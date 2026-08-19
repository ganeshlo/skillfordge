from django.urls import path

from .views import (
    CancelSubscriptionView,
    CreateOrderView,
    InvoiceListView,
    PaymentCancelView,
    PaymentHistoryView,
    PlanListView,
    RazorpayWebhookView,
    SubscriptionView,
    VerifyPaymentView,
)

urlpatterns = [
    path("billing/plans/", PlanListView.as_view(), name="billing-plans"),
    path("billing/orders/", CreateOrderView.as_view(), name="billing-create-order"),
    path("billing/payments/verify/", VerifyPaymentView.as_view(), name="billing-verify-payment"),
    path("billing/payments/", PaymentHistoryView.as_view(), name="billing-payment-history"),
    path("billing/payments/<uuid:payment_id>/cancel/", PaymentCancelView.as_view(), name="billing-payment-cancel"),
    path("billing/subscription/", SubscriptionView.as_view(), name="billing-subscription"),
    path("billing/subscription/cancel/", CancelSubscriptionView.as_view(), name="billing-subscription-cancel"),
    path("billing/invoices/", InvoiceListView.as_view(), name="billing-invoices"),
    path("billing/webhooks/razorpay/", RazorpayWebhookView.as_view(), name="billing-razorpay-webhook"),
]
