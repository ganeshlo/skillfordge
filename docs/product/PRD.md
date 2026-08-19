# LearnOS Product Requirements Document

## Product statement

LearnOS is a personal and enterprise learning operating system that brings learning plans, resources, focused study, notes, coding practice, projects, AI assistance, goals, and evidence-based progress into one secure workspace.

## Problem

Learners currently split their work across video platforms, note tools, code editors, task managers, course platforms, and spreadsheets. Progress data becomes incomplete, study context is lost, and managers see completions rather than demonstrated capability. LearnOS provides a single workflow while preserving user privacy and tenant boundaries.

## Primary outcomes

1. A learner can move from a career goal to an editable roadmap and a clear next action.
2. Learning activity is measured from real engagement, not superficial completion signals.
3. Notes, assessments, code, and projects become evidence for an explicitly estimated readiness score.
4. AI answers are grounded in authorized sources and cite them.
5. Organizations can assign and aggregate learning without automatically accessing private notes or code.
6. High-risk workloads such as user code execution are isolated from the application plane.

## Personas and jobs to be done

| Persona | Primary job |
|---|---|
| Student / job seeker | Build a guided plan, stay consistent, create portfolio evidence, prepare for interviews |
| Developer / professional | Close skill gaps, practice, build projects, retain knowledge |
| Mentor / instructor | Assign content, review permitted evidence, give feedback |
| Manager / learning administrator | Assign paths, understand aggregate progress, manage compliance |
| Organization administrator | Manage tenants, teams, policy, integrations, exports, and audit records |
| Platform administrator | Operate tenants, plans, moderation, health, and system policy |

## Product principles

- Private by default; organization visibility is explicit and policy-controlled.
- Evidence over vanity metrics.
- AI augments learning but does not silently make authoritative judgments.
- Modular monolith first; independently dangerous or elastic workloads are separate services.
- Accessibility, keyboard support, and responsive behavior are acceptance criteria.
- Every privileged operation is authorized server-side and auditable.

## Scope and releases

### MVP

Identity, onboarding, tenant foundation, dashboard, roadmaps, topics, resources, notes, study sessions, goals, basic analytics, notifications, audit trail, and AI provider abstraction.

### Subsequent releases

YouTube interval tracking; coding workspace and isolated runners; grounded AI tutor, quizzes and flashcards; projects and GitHub; career readiness; enterprise LMS and advanced reporting.

## Success metrics

- Activation: onboarding completed and first roadmap created within 24 hours.
- Learning: weekly active study minutes, topics completed with evidence, and 4-week retention.
- Quality: AI answer citation rate, video-progress integrity, and task completion success.
- Reliability: API availability, job latency, execution cleanup success, error budget.
- Enterprise: assigned-path completion, active seats, and audit/export success.

## Explicit non-goals for MVP

- Hosting or redistributing YouTube media.
- Arbitrary dependency installation in code runners.
- Scientific or employment-decision claims from readiness scores.
- Access by organizations to private personal content without an explicit policy and consent basis.
- Premature decomposition of every domain into a network service.

## Release gates

No phase ships without tenant-isolation tests, authorization tests, migration rollback review, operational metrics, accessible error/empty/loading states, and documented data-retention behavior.

