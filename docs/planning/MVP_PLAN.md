# MVP Implementation Plan

## Delivery sequence

1. Foundation: identity, profile/onboarding, organization tenancy, roles/policies, audit/request IDs, API contracts, design system, CI.
2. Learning core: roadmaps, hierarchy, resources, assignments, progress events, dashboard next action.
3. Study core: notes, study timer, goals, privacy controls, basic analytics.
4. YouTube: metadata ingestion, iframe workspace, interval tracking, timestamped notes/bookmarks.
5. Coding: Monaco projects, independent Python/JavaScript execution controller and runner pool.
6. AI: provider abstraction, usage ledger, grounded tutor, roadmap/quiz/flashcard generation.
7. Professional: challenges, project management, GitHub, readiness estimate.
8. Enterprise: teams, content assignment, aggregate reporting, audit UI, SSO readiness and branding.

## Milestone exit criteria

Every milestone requires API and permission tests, tenant-isolation tests, accessible UX states, structured events, migration review, operational probes, and documentation. Risky services require threat-model tests before feature tests are accepted.

## Technical dependencies

- Identity and tenancy precede every shared domain.
- Learning hierarchy precedes video, assessments, and recommendation context.
- Activity events precede analytics and readiness estimates.
- Document authorization precedes embeddings/RAG.
- Execution job contracts precede runner implementation.

