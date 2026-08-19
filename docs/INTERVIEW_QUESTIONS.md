# LearnOS interview questions and answers

These questions cover the product, architecture, backend, frontend, security, testing, and operational decisions in this repository. Each answer is intentionally concise so it can be expanded during an interview with an example from the codebase.

## Product and architecture

### 1. What problem does LearnOS solve?

It combines roadmaps, focused study, notes, coding practice, goals, progress evidence, and subscriptions in one learning workspace. Its key product distinction is evidence-based progress with private-by-default learner data.

### 2. Why use a modular monolith for Django?

The product domains change together and benefit from local transactions, one deployment model, and simpler operations. Domain packages still create clear ownership boundaries and can be extracted later if scale or team ownership justifies the network cost.

### 3. Why is code execution a separate service?

Running untrusted code has a fundamentally different threat model and scaling profile. Separating the controller keeps the Docker socket and sandbox lifecycle away from the API and lets execution capacity scale independently.

### 4. What are the main system components?

Next.js provides the web UI, Django REST Framework owns business APIs, PostgreSQL stores durable state, Redis/Celery handle asynchronous work, and the execution controller creates restricted ephemeral runner containers.

### 5. What is the standard request lifecycle?

A request receives a request ID, authenticates the caller, resolves tenant context, validates input, checks permissions and visibility, invokes a domain service transaction, records required audit effects, and returns a stable response.

### 6. When would you split another service from Django?

Only when a domain has an independently valuable boundary: a distinct security model, large or unpredictable scaling needs, independent availability requirements, or clear team ownership. Splitting merely by noun adds network and consistency complexity.

## Backend and data

### 7. Why keep business workflows out of Django views?

Thin views make behavior reusable by APIs, background tasks, and administrative commands. Domain services define transaction boundaries and are easier to test without transport details.

### 8. How is tenant isolation enforced?

Protected queries require the authenticated principal and validated membership/tenant context. Owner or organization predicates are applied before object retrieval, uniqueness includes tenant keys, and adversarial tests cover cross-tenant identifiers.

### 9. What is the difference between authentication and authorization?

Authentication proves the caller's identity. Authorization combines that identity with membership, tenant, permission, object visibility, ownership, and resource state to decide whether an operation is allowed.

### 10. Why use UUID primary keys?

UUIDs avoid exposing simple record counts, can be generated across distributed producers, and reduce collision risk during merges. They do not replace authorization; every UUID lookup still needs an ownership or tenant filter.

### 11. Why are idempotency keys important?

Clients and queues retry when responses are lost. An idempotency key lets the server recognize the same logical command and reuse its result instead of creating duplicate executions, invitations, imports, or payments.

### 12. How should a Celery task be designed for retries?

Persist intent before dispatch, pass stable record IDs, validate the current state, make effects idempotent, use bounded retries with backoff, and store a safe terminal error when recovery is exhausted.

### 13. How is video completion calculated accurately?

Playback intervals are clamped to video duration, sorted, merged when overlapping or adjacent, and summed once. Completion is unique watched seconds divided by duration, not the furthest playback position.

### 14. Why create immutable code revisions?

Revisions provide traceability, recovery, and evidence of how a project changed. A checksum prevents unchanged autosaves from producing meaningless versions.

### 15. What data should never be stored in generic JSON fields?

Passwords, provider secrets, OAuth tokens, payment credentials, MFA secrets, and other restricted credentials. They need dedicated encrypted storage, limited access paths, rotation, and audit controls.

## Frontend

### 16. Why use Next.js and TypeScript strict mode?

Next.js supports routing, static and server rendering, production bundling, and a mature React ecosystem. Strict TypeScript catches contract and nullability errors before runtime and improves safe refactoring.

### 17. How does the code editor avoid losing work?

Monaco updates local draft state immediately, saves after a debounce, exposes an explicit save shortcut, and reflects saved/unsaved state. The server creates a revision only when content actually changes.

### 18. Why are loading, empty, error, and success states separate?

They represent different user decisions. A skeleton prevents layout shifts, an empty state explains the first action, an error offers recovery, and success renders real data without ambiguous placeholders.

### 19. Why must client-side role checks not be the security boundary?

Browser code can be modified and API requests can be sent directly. Client checks improve the interface, but the backend must independently authorize every protected read and mutation.

### 20. How should access-token expiration be handled?

The client should attempt one controlled refresh, retry eligible requests once, coordinate concurrent refreshes, and return to sign-in if refresh fails. It must avoid infinite retry loops.

### 21. Why use a sandboxed iframe for HTML/React preview?

It separates learner-authored browser code from the application origin. The preview should not inherit authentication, same-origin storage, or unrestricted navigation permissions.

## Secure code execution

### 22. What prevents user code from compromising the platform?

User code runs only in short-lived containers with network disabled, capabilities dropped, a read-only root filesystem, bounded CPU/memory/processes/time/output, no application secrets, and forced cleanup.

### 23. Why does the controller receive signed requests?

An HMAC signature lets the controller reject callers that do not possess the shared secret and detects payload modification. Deployment networking should additionally restrict who can reach the controller.

### 24. Why not run code inside Celery?

Celery shares application dependencies, credentials, database access, and a long-lived worker process. A sandbox escape or resource-exhaustion bug there would directly compromise the application plane.

### 25. What does “fail closed” mean for execution?

If controller configuration or sandbox readiness is missing, Run is unavailable and no local fallback evaluates source in Django or the worker. Editing and saving continue to work safely.

### 26. How do Run and Stop avoid race conditions?

Execution uses a persisted state machine and idempotent job creation. Cancellation checks current state, records intent, asks the controller to stop the matching job, and treats already-terminal jobs consistently.

## Knowledge and AI

### 27. How would retrieval-augmented generation be secured?

Authorize sources before retrieval, filter chunks by owner/tenant, treat documents as untrusted input, bound context, label AI output, cite source records, and log usage without storing restricted prompts unnecessarily.

### 28. What happens when no AI key is configured?

The feature returns a clearly labeled demo/fallback result or a controlled unavailable response. It must never fabricate a successful provider call or expose configuration details.

### 29. How do you prevent one learner from searching another learner's notes?

Access filtering occurs in the database query before ranking or embedding retrieval. Filtering results after vector search can leak identifiers, counts, or content through side channels.

## Billing

### 30. Why does the browser submit a plan code instead of an amount?

The browser is untrusted and amounts are easy to modify. Django loads the active plan and authoritative minor-unit price before creating the provider order.

### 31. When is a paid subscription activated?

Only after Django verifies the Checkout signature and captured provider state, or after it processes a valid signed capture webhook. A browser success screen alone is not proof of payment.

### 32. Why are webhooks deduplicated?

Providers retry events and may deliver them out of order. A unique provider event ID plus state-aware handlers prevents duplicate invoices, repeated activation, or incorrect transitions.

### 33. Does LearnOS store card or UPI credentials?

No. Razorpay Checkout collects them directly. LearnOS stores only limited provider identifiers, amount, currency, status, and non-sensitive reconciliation information.

## Testing, CI/CD, and operations

### 34. What does the CI pipeline verify?

It runs backend lint, Django system checks, tests, and OpenAPI validation; frontend lint, type checking, tests, and production build; controller tests; and Docker builds. Successful pushes to `main` publish versioned images.

### 35. Why should lint rules be explicit in the repository?

Tool defaults can change between versions. A checked-in rule selection makes developer machines and CI evaluate the same policy and turns rule expansion into a reviewed change.

### 36. What is the difference between liveness and readiness?

Liveness answers whether the process is running and can be restarted if it is stuck. Readiness answers whether dependencies are usable and whether the instance should receive traffic.

### 37. What should be tested for a tenant-owned endpoint?

Happy path, unauthenticated access, missing permission, a different tenant's identifier, private versus shared visibility, invalid payloads, pagination/filter bounds, and relevant audit/idempotency behavior.

### 38. Why validate the OpenAPI schema in CI?

It detects serializer/view contract problems before deployment and keeps generated client/documentation contracts aligned with the actual API.

### 39. How would you diagnose a production request failure?

Start with the request ID, correlate ingress and application logs, inspect status/latency and dependency metrics, identify the domain state transition, and use audit/job records without exposing sensitive payloads.

### 40. How would the platform scale?

Scale stateless web instances, Celery queues by workload, database reads and indexes based on measured queries, and execution runners independently. Add caching or service extraction only after observing a specific bottleneck.

## Scenario questions to practice

1. A learner clicks Run twice because the first response is slow. Walk through the idempotent behavior.
2. A manager guesses another organization's roadmap UUID. Explain every layer that prevents disclosure.
3. Razorpay sends `payment.captured` twice and then an older `payment.failed` event. Design the state transitions.
4. Redis becomes unavailable during a document upload. Which data is durable, and what does the learner see?
5. A sandbox process forks repeatedly and prints unlimited output. Which controls stop it?
6. Two browser tabs refresh an expired token simultaneously. How should the client coordinate them?
7. An AI document contains instructions to reveal other users' notes. How does authorized retrieval and prompt isolation respond?
8. A new Ruff release enables hundreds of rules in CI but not locally. How do you restore deterministic checks and review new rules safely?
9. Video interval events arrive twice and out of order. Demonstrate the merge calculation.
10. The database is live but Redis is unavailable. What should liveness and readiness return, and why?
