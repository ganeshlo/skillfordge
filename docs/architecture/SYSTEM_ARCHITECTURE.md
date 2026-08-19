# System Architecture

## Context diagram

```text
Browser / Mobile Web
        |
        v
CDN + WAF + TLS
        |
        +---------------- Next.js web application
        |
        v
Nginx / API ingress ---- request ID, limits, routing
        |
        v
Django modular monolith (REST + WebSocket gateway)
  | accounts | organizations | permissions | learning | roadmaps |
  | content | videos | study | notes | quizzes | flashcards |
  | coding | projects | goals | analytics | AI | integrations |
  | notifications | audit | subscriptions |
        |              |                 |
        v              v                 v
  PostgreSQL       Redis/queue       Object storage
   + pgvector        + cache          + signed URLs
        |              |
        |              +------ Celery workers (AI, documents, notifications, analytics)
        |
        +-------------------- read replicas / warehouse export (later)

Dedicated execution control service
        |
        v
Execution queue -> isolated runner pool -> ephemeral unprivileged sandbox
                                           (network off, quotas, cleanup)

External systems: OpenAI-compatible providers, YouTube APIs/player,
GitHub, email provider, OAuth/SSO providers, metrics/error platforms.
```

## Deployment boundary decisions

- The Django application begins as a modular monolith to keep transactions and domain evolution manageable.
- Code execution is separate from day one because its threat model and scaling profile differ fundamentally.
- Web, background workers, scheduler, and WebSocket workers are separate deployable processes from one backend codebase.
- AI providers, embedding stores, object stores, queues, and identity providers sit behind ports/adapters.

## Backend rules

Each domain owns models, policies, selectors/query services, commands/services, tasks, API serializers/views, and tests. Cross-domain effects emit an outbox event inside the source transaction. Background consumers are idempotent.

Views may authenticate, validate transport input, invoke a service, and serialize output. They do not contain business workflows. Selectors always accept a principal/tenant context for tenant data.

## Request lifecycle

```text
Ingress -> request ID -> authentication -> tenant resolution -> throttling
-> serializer validation -> permission policy -> domain service transaction
-> outbox/audit event -> response envelope -> structured access log
```

## Technology baseline

- Next.js, React, TypeScript strict mode, Tailwind, TanStack Query, React Hook Form/Zod, Monaco, Recharts.
- Django/DRF, Channels, Celery, Redis, PostgreSQL/pgvector.
- OpenAPI/Redoc, structured logging, Prometheus-ready metrics, Sentry-ready exception adapter.
- Docker Compose locally; Kubernetes-ready containers, probes, config, secrets, and autoscaling.

