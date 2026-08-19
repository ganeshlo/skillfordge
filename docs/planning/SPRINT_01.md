# Sprint 01 — Secure Foundation

## Goal

A user can create an account, authenticate, complete onboarding, create an organization, and access a tenant-aware shell. All actions have request IDs and critical mutations are auditable.

## Backlog

| Priority | Story | Acceptance criteria |
|---|---|---|
| P0 | Custom UUID user and profile | normalized email, password hashing, profile/preferences, migration tests |
| P0 | JWT authentication | access/rotating refresh, throttled endpoints, invalid/reused token rejection |
| P0 | Onboarding | typed validated payload, idempotent completion, career and study preferences |
| P0 | Organization tenancy | UUID organization, unique slug, membership, role, active tenant validation |
| P0 | Server authorization | membership and permission policies; cross-tenant tests |
| P0 | Audit/request context | request ID in responses/logs; register/onboard/org events recorded |
| P0 | API documentation | `/api/schema/` and `/api/docs/`; CI schema validation |
| P1 | LearnOS web shell | landing, auth, onboarding, empty-state dashboard, responsive navigation |
| P1 | Local infrastructure | PostgreSQL, Redis, backend, Next.js; health/readiness probes |
| P1 | Seed command | deterministic demo organization/user only for development |
| P1 | Quality gates | Ruff, backend tests, TypeScript/lint/build, container builds |

## Not in this sprint

Social OAuth provider handshakes, MFA enrollment, roadmaps, learning content, code execution, YouTube tracking, or AI chat. Their contracts are anticipated but not faked.

