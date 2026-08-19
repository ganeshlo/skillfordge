# Payment and Subscription Module

## Architecture

The `billing` Django domain owns all commercial state. The browser sends only a plan code; Django loads the active `Plan` row and uses its integer minor-unit amount and currency. Provider-specific calls live behind `RazorpayGateway`, while subscriptions, payments and invoices use provider-neutral models.

```text
Pricing card
  -> POST /api/v1/billing/orders/ { plan_code }
  -> Django loads server Plan price
  -> Razorpay Orders API
  -> official Razorpay Checkout
  -> POST /api/v1/billing/payments/verify/
  -> HMAC verification + provider payment validation
  -> activate Subscription + create Invoice + AuditLog

Razorpay webhook
  -> verify HMAC over raw request bytes
  -> deduplicate X-Razorpay-Event-Id
  -> update Payment / Subscription / Invoice
```

The application never receives or stores card, bank or UPI credentials. It stores provider order/payment identifiers, status, amount, currency, and a limited non-sensitive provider summary.

## Configuration

Create Razorpay test credentials and a separate webhook secret, then set:

```env
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
RAZORPAY_API_URL=https://api.razorpay.com/v1
RAZORPAY_TIMEOUT_SECONDS=10
```

Never expose `RAZORPAY_KEY_SECRET` or `RAZORPAY_WEBHOOK_SECRET` to Next.js. The API returns only the publishable Key ID to Checkout.

Configure this webhook URL in the Razorpay test dashboard:

```text
https://your-api.example.com/api/v1/billing/webhooks/razorpay/
```

Subscribe to `payment.captured`, `payment.failed`, `order.paid`, `refund.created`, `refund.processed`, `refund.failed`, and relevant `subscription.*` events. Use separate test and live webhooks and secrets.

## APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/billing/plans/` | Active server plans |
| POST | `/billing/orders/` | Create server-priced order |
| POST | `/billing/payments/verify/` | Verify Checkout signature and activate |
| GET | `/billing/subscription/` | Current user subscription |
| POST | `/billing/subscription/cancel/` | Cancel at period end |
| GET | `/billing/payments/` | User-scoped payment history |
| POST | `/billing/payments/{id}/cancel/` | Record Checkout dismissal |
| GET | `/billing/invoices/` | User-scoped invoices |
| POST | `/billing/webhooks/razorpay/` | Signed provider events |

Authenticated endpoints derive the user from JWT and never accept a user ID. The webhook endpoint does not use user authentication because it authenticates Razorpay using the raw-body signature.

## Data model

- `Plan`: server price, currency, duration, features and availability.
- `Payment`: immutable charged amount plus provider IDs and verified lifecycle status.
- `Subscription`: access period, current plan, cancellation and provider state.
- `Invoice`: one verified payment receipt associated with its subscription.
- `WebhookEvent`: signed event payload, processing status and unique provider event ID.

Free activation creates no payment. Paid subscriptions are activated only after a captured provider payment or a valid signed capture webhook. Activating a new plan expires the previous active subscription transactionally.

## Extension to another gateway

Implement the same operations as `RazorpayGateway`, add a provider resolver, and keep the service layer and database models unchanged. Provider payloads must be reduced to non-sensitive fields before persistence.

## Testing

Backend tests mock the gateway and verify server-authoritative pricing, idempotency, signature rejection, activation/invoice creation, user isolation and webhook signature/deduplication. Frontend component tests cover pricing selection, secure Checkout messaging and cancellation state.
