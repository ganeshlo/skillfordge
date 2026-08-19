# Functional and Non-Functional Requirements

## Functional requirements by domain

| Domain | MVP capability | Later capability |
|---|---|---|
| Identity | Email registration, verification architecture, JWT rotation, password reset architecture, profile, onboarding, session inventory | OAuth, MFA, enterprise SSO, suspicious-login automation |
| Tenancy | Organizations, memberships, role assignment, tenant context, privacy policy flags | departments, cohorts, branding, SCIM |
| Learning | Roadmaps, phases, modules, topics, resources, dependencies, milestones, progress | templates, cloning, assignment, recommendations |
| Study | Timed sessions, pause/resume, active/idle duration, goals, notes | Pomodoro, offline sync, advanced focus analysis |
| Content | Links and documents with validation and access policy | extraction, object storage, content pipelines |
| Video | URL ingestion and official embed | interval union, bookmarks, transcript-grounded AI |
| Knowledge | Markdown/rich notes, tags, links, private-by-default permissions | embeddings, semantic retrieval, source-cited answers |
| Assessment | authored quizzes and attempts | AI generation, adaptive questions, spaced repetition |
| Coding | project metadata and files | Monaco IDE, challenges, isolated execution service |
| AI | provider-neutral request contract, usage ledger, safety boundary | tutor graph, RAG, quiz/roadmap/code agents |
| Analytics | event collection and dashboard aggregates | cohort comparisons, readiness estimate, exports |
| Operations | notifications, audit logs, health/readiness | billing, admin health, advanced observability |

## Cross-cutting behavior

- All externally exposed APIs are under `/api/v1/`.
- Collection endpoints paginate, filter, and sort through allowlisted fields.
- Mutating endpoints validate tenant membership and domain permissions.
- Retryable commands accept an idempotency key where duplicate effects matter.
- Errors use a stable code, human message, field details, and request ID.
- Dates are stored in UTC and rendered in the user's timezone.
- Soft-deleted records are excluded by default and retained per policy.

## Non-functional requirements

| Area | Target / rule |
|---|---|
| Availability | 99.9% monthly for the application API after general availability |
| API latency | p95 below 400 ms for normal reads; long work becomes an asynchronous job |
| Scalability | stateless web nodes, horizontal Celery workers, partitionable analytics events |
| Security | OWASP ASVS-aligned controls, least privilege, short-lived access tokens, rotated refresh tokens |
| Tenant isolation | tenant predicates in query services plus adversarial cross-tenant tests |
| Privacy | private notes/code by default; purpose-limited events; export and deletion workflows |
| Accessibility | WCAG 2.2 AA target; keyboard and screen-reader acceptance checks |
| Recovery | production RPO ≤ 15 minutes and RTO ≤ 4 hours; restore drills required |
| Observability | structured logs, request IDs, metrics, traces/error abstraction, audit events |
| Maintainability | typed boundaries, domain modules, migration review, architecture decision records |
| AI safety | source authorization before retrieval, usage limits, injection defenses, output labeling |
| Code execution | no execution on API hosts; deny network and host access; enforced resource budgets |

## Data classification

- Public: published roadmaps and intentionally public profiles.
- Internal: course metadata and aggregate metrics.
- Confidential: personal learning history, private notes, code, assessment answers.
- Restricted: password hashes, OAuth/API tokens, MFA secrets, enterprise identity assertions.

Restricted data is encrypted at rest with managed keys where field-level protection is required and is never returned to browser clients after initial exchange.

