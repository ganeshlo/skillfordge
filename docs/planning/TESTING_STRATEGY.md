# Testing Strategy

- Unit: domain validation, permission policies, interval merging, schedulers, readiness formula.
- API: validation, envelopes, pagination, throttling, idempotency, JWT rotation.
- Isolation: a matrix of users, tenants, roles, object privacy, and support access.
- Integration: PostgreSQL constraints, Redis/Celery tasks, outbox delivery, storage adapters.
- Security: auth abuse, upload validation, injection, SSRF, token handling, dependency scanning.
- AI: fake adapters, authorized retrieval, citation completeness, limits, prompt-injection fixtures.
- Execution: hostile corpus, network/host denial, resource limits, cancellation, orphan cleanup.
- Frontend: React Testing Library for states/forms; Playwright for onboarding and core journeys.
- Operations: migration rehearsal, backup restore, probe failure, worker retry and dead-letter behavior.

CI layers fast unit/API tests before builds. Nightly jobs run heavier isolation, browser, and security suites. Production releases require migration and rollback evidence.

