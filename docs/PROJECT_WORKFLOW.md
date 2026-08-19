# LearnOS end-to-end workflow

This document explains how a learner request moves through LearnOS, from account creation to learning evidence, code execution, billing, and deployment. Detailed subsystem documents are linked where a workflow has additional security or implementation rules.

## 1. Platform at a glance

```text
Learner / mentor / administrator
              |
              v
       Next.js web application
              |
              | HTTPS + JSON + JWT
              v
       Django REST API (/api/v1)
     /         |          |         \
PostgreSQL   Redis     Celery     Audit log
                           |
                           +---- document and AI background work
                           |
                           +---- signed execution request
                                      |
                                      v
                            Execution controller
                                      |
                                      v
                         Ephemeral restricted container
```

The Django backend is a modular monolith. Accounts, organizations, roadmaps, study, knowledge, coding, goals, dashboard, and billing remain separate domains inside one transactional application. Code execution is a separate service because it has a different security and scaling boundary.

## 2. Complete learner journey

```text
Register -> sign in -> complete onboarding
    -> create a goal and roadmap
    -> choose a topic and learning resource
    -> study video/document and capture notes
    -> practice in the coding workspace
    -> save revisions and execution evidence
    -> review dashboard progress
    -> adjust goals and continue the next topic
    -> optionally upgrade a subscription
```

### Step 1: Identity and session

1. The learner registers with email, password, and profile data.
2. Django validates and hashes the password; raw passwords are never stored.
3. Sign-in returns a short-lived access JWT and a refresh-token workflow.
4. The frontend sends the access token for protected API calls.
5. Every protected view derives the user from authentication. It does not trust a user ID supplied by the browser.

### Step 2: Onboarding

1. The learner provides role, experience, interests, target skills, and preferences.
2. The API validates the payload and updates the user profile transactionally.
3. Completion changes the next frontend destination from onboarding to the dashboard.
4. Preferences become inputs to roadmap and learning recommendations; they are not treated as proof of skill.

### Step 3: Goals, roadmap, and dashboard

1. The learner creates a measurable goal with dates, priority, and status.
2. A roadmap organizes work into phases, modules, and topics.
3. Ownership and organization visibility are checked on every roadmap read or mutation.
4. The dashboard combines current goals, roadmap progress, activity, and recommended next actions.
5. Progress is calculated from stored learning evidence rather than a client-only completion flag.

### Step 4: Study workspace

1. The learner chooses an accessible roadmap topic.
2. The learner adds or selects a validated YouTube resource; LearnOS stores the video ID and uses the official embedded player.
3. The player records bounded playback intervals with idempotent event IDs.
4. Django clamps and merges overlapping intervals so replayed sections are counted once.
5. Notes and bookmarks are saved with the current timestamp and remain scoped to their owner.
6. Completion requires the configured percentage of unique watched duration.

See [Study Workspace](study-workspace/ARCHITECTURE.md) for the playback and persistence details.

### Step 5: Knowledge workspace

1. The learner creates notes, snippets, video references, or document records.
2. Upload validation checks type, size, access, and ownership before processing.
3. Expensive extraction, indexing, and AI work is dispatched to Celery.
4. Search retrieves only records the authenticated learner is allowed to read.
5. AI notes use the configured provider when available and a clearly labeled fallback when it is not.
6. Provider keys remain on the backend and are never serialized to the browser.

### Step 6: Coding workspace

1. The learner creates a project from a supported language template.
2. Monaco keeps an unsaved local draft and periodically saves through the files API.
3. Each changed save updates the checksum and creates an immutable revision.
4. A Run request first saves current source, then creates an idempotent execution job.
5. Celery signs and sends the job to the execution controller.
6. The controller starts an ephemeral language container with no network, a read-only root filesystem, dropped capabilities, and CPU, memory, time, process, and output limits.
7. Django polls the controller and persists only bounded output and execution metrics.
8. The frontend renders queued, running, succeeded, failed, cancelled, or timed-out state.
9. HTML, CSS, and React use a sandboxed browser preview instead of server execution.

See [Code Workspace Workflow](CODE_WORKSPACE_WORKFLOW.md) for editor controls and the detailed execution sequence.

### Step 7: Billing and entitlements

1. The pricing screen loads active plans and server-owned prices.
2. The browser submits only a plan code; it cannot choose the charged amount.
3. Django creates a Razorpay order and returns the publishable checkout data.
4. Razorpay Checkout collects payment credentials directly.
5. Django verifies the signature and provider payment state before activating access.
6. A successful capture creates or updates the payment, subscription, invoice, entitlements, and audit record transactionally.
7. Signed webhook events reconcile delayed, failed, refunded, or subscription lifecycle changes and are deduplicated by provider event ID.

See [Payment and Subscription Module](PAYMENT_SUBSCRIPTION.md) for gateway configuration and webhook rules.

## 3. API request lifecycle

Every protected API request follows the same boundary:

```text
HTTP request
  -> request ID
  -> authentication
  -> tenant and membership resolution
  -> serializer validation
  -> permission and object-visibility policy
  -> domain service transaction
  -> audit/outbox side effect where required
  -> stable response envelope
  -> structured access log
```

- Validation failures return field-level information without changing state.
- Authentication answers who the caller is; authorization decides whether that caller may perform the operation.
- Tenant context is validated against active membership and never accepted solely from request JSON.
- Retryable side effects use an `Idempotency-Key` so network retries do not create duplicates.
- Long-running work returns a job record and is completed asynchronously.

## 4. Background-job lifecycle

```text
API transaction -> durable domain/job row -> Celery queue -> worker
     -> external provider or internal processor
     -> idempotent state update -> client polling/refresh
```

Workers receive record identifiers rather than trusting a large browser payload. A task can be retried only when its effect is idempotent or guarded by a unique key/state transition. Failed jobs retain a safe error summary for user feedback and operational diagnosis.

## 5. Data ownership and permissions

The authorization decision combines:

```text
authenticated user
  + active organization membership
  + tenant
  + permission
  + object ownership/visibility
  + current resource state
```

- Personal notes, study activity, and code are private by default.
- Organization membership does not automatically expose private learner content.
- Managers receive aggregate progress unless evidence was explicitly shared.
- Tenant-owned uniqueness constraints include the organization key.
- API selectors apply owner or tenant filters before fetching an object, preventing cross-tenant identifier probing.
- Privileged state changes create audit records.

## 6. Failure and recovery behavior

| Failure | Expected behavior |
|---|---|
| Invalid or expired access token | Return 401; the client refreshes or asks the user to sign in |
| Permission or ownership failure | Return 403/404 without leaking another tenant's data |
| Duplicate request | Return/reuse the idempotent result instead of duplicating the effect |
| Redis or worker unavailable | Keep the durable job queued/failed and show a retryable status |
| AI provider unavailable | Preserve user data and return a labeled fallback or controlled error |
| Execution backend unavailable | Fail closed; editing and saving remain available |
| Sandbox exceeds a limit | Terminate it and record timed-out/failed bounded output |
| Payment callback is interrupted | Reconcile through the signed webhook |
| Database readiness fails | Readiness returns non-200 so traffic is not routed to the instance |

## 7. Local development workflow

```bash
cp .env.example .env
docker compose --profile runner-images build kotlin-runner-image
docker compose up --build
```

The web application runs at `http://localhost:3000`, Django at `http://localhost:8000`, API documentation at `http://localhost:8000/api/docs/`, and the execution controller at `http://localhost:8080`.

For a normal change:

1. Create a focused branch.
2. Update the domain service, API contract, UI, and tests that belong to the behavior.
3. Run backend lint/check/tests and OpenAPI validation.
4. Run frontend lint, type checking, tests, and production build.
5. Run execution-controller tests when its boundary changes.
6. Build Docker images when dependencies, runtime configuration, or Dockerfiles change.
7. Open a pull request and merge only after CI passes.

## 8. CI/CD workflow

```text
Push / pull request
  -> backend: Ruff, Django checks, tests, OpenAPI validation
  -> frontend: ESLint, TypeScript, Vitest, Next.js production build
  -> execution controller: pytest
  -> Docker image builds
  -> main only: publish versioned images to GHCR
```

CI does not auto-fix source files. Developers apply fixes locally, review the diff, and commit them. Tool policies are stored in the repository so a dependency update cannot silently change the enabled lint rules.

## 9. Production request path

1. DNS routes the product domain to a CDN/WAF and TLS endpoint.
2. Static Next.js assets are cached; dynamic application traffic reaches the web service.
3. `/api/v1` traffic reaches stateless Django instances through an ingress.
4. Django uses PostgreSQL for durable state and Redis for cache/queues.
5. Celery workers scale separately from web requests.
6. Execution-controller capacity and sandbox runners scale independently from the application plane.
7. Health probes, structured request IDs, metrics, error reporting, audit logs, backups, and restore tests provide operational control.

Production must replace every development secret, disable Django debug mode, restrict allowed hosts and origins, enforce HTTPS, use managed data services, and apply least-privilege credentials.
