# API Specification

## Conventions

- Base path: `/api/v1`.
- Authentication: short-lived bearer access JWT; rotated refresh token in an HttpOnly Secure SameSite cookie for the web client.
- Tenant context: route-scoped where practical, otherwise `X-Organization-ID`, validated against active membership.
- Success: `{ "data": ..., "meta": { ... }, "request_id": "..." }`.
- Error: `{ "error": { "code": "...", "message": "...", "fields": {} }, "request_id": "..." }`.
- Cursor pagination for event feeds; page-number pagination for stable administration lists.
- `Idempotency-Key` required for invitations, AI generation jobs, code execution, billing, and imports.

## Initial identity endpoints

| Method | Route | Purpose |
|---|---|---|
| POST | `/auth/register/` | Create an unverified account and profile |
| POST | `/auth/token/` | Issue access and refresh token pair |
| POST | `/auth/token/refresh/` | Rotate refresh token |
| POST | `/auth/token/revoke/` | Revoke a refresh token/session |
| GET/PATCH | `/me/` | Current profile and preferences |
| POST | `/me/onboarding/` | Validate and complete onboarding |
| GET | `/me/sessions/` | Device/session inventory |
| GET/POST | `/organizations/` | List memberships or create organization |
| GET | `/organizations/{id}/members/` | Permission-scoped member listing |
| GET | `/health/live/` | Process liveness |
| GET | `/health/ready/` | Database/Redis readiness |

## Domain route families

`roadmaps`, `courses`, `topics`, `resources`, `videos`, `study-sessions`, `notes`, `search`, `quizzes`, `flashcards`, `coding-problems`, `execution-jobs`, `projects`, `goals`, `analytics`, `ai`, `integrations/github`, `notifications`, `admin`, and `audit-logs`.

OpenAPI is generated from serializers and view contracts. CI fails on schema-generation errors and publishes versioned API documentation.

