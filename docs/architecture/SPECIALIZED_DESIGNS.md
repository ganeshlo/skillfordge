# AI, Video, and Code Execution Designs

## AI architecture

```text
Feature command -> authorization/context builder -> retrieval policy
-> provider-neutral orchestration -> model adapter -> safety/output validation
-> cited answer + usage ledger + audit/event metadata
```

The context builder receives authorized resource IDs, not an unrestricted tenant search. Retrieval filters are applied before vector similarity. Each output stores provider/model, prompt-template version, latency, token estimates, cost metadata, safety result, and source references. Provider keys remain server-side. Hosted and local adapters implement the same interface. Expensive work is queued and cancellable.

Prompt injection is treated as untrusted content: retrieved text cannot change system policy or tool permissions. Tools use narrow schemas and re-authorize every read/write. The tutor never reveals system prompts, credentials, cross-tenant content, or hidden assessment answers.

## YouTube tracking

Use the official iframe player and supported metadata APIs; never download video media. The browser emits signed/authorized progress batches containing monotonic session time, player state, speed, and small watched intervals. The server validates bounds, rate, sequence, and plausible elapsed time, then unions intervals transactionally.

```text
play -> sample contiguous intervals -> pause/seek/visibility/idle split interval
-> batch -> validate -> merge existing intervals -> recompute unique coverage
```

Seeking creates no watched interval. Hidden/idle periods do not count as active study. Completion thresholds require sufficient unique coverage, not reaching the final timestamp.

## Code execution security

```text
API -> validate language/size/rate -> durable ExecutionJob -> queue
-> execution controller -> ephemeral sandbox -> capture bounded output
-> persist sanitized result -> destroy sandbox -> cleanup reconciler
```

Runners are unprivileged, rootless where supported, read-only, network-denied, capability-dropped, seccomp/AppArmor constrained, and assigned CPU/memory/PID/time/file/output limits. They receive no host mount, Docker socket, instance metadata, cloud credential, application database, or secret environment. Images are pinned, scanned, signed, and language-allowlisted. Cancellation and orphan cleanup are mandatory. The first runner release supports Python and JavaScript only and disables package installation.

