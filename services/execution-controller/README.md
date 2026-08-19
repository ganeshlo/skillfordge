# LearnOS Execution Controller

This service validates signed internal requests and delegates jobs to a sandbox backend. It never evaluates user source itself and has no unsafe local-subprocess mode.

Two backends are supported:

- `SANDBOX_BACKEND=docker` creates an ephemeral allowlisted language container for each local-development job. The controller receives the Docker socket, but user-code containers never do.
- A remote backend delegates to a separately hardened provider using `SANDBOX_PROVIDER_URL` and `SANDBOX_PROVIDER_TOKEN`.

Every user-code container has network mode `none`, a read-only root filesystem, an unprivileged user, all capabilities dropped, `no-new-privileges`, and bounded CPU, memory, PID count, runtime, input, and output. Source and stdin are transferred through a temporary read-only volume and all containers and volumes are removed after completion.

Build the native multi-architecture Kotlin runner once before starting the stack:

```bash
docker compose --profile runner-images build kotlin-runner-image
```

Required environment variables:

```text
EXECUTION_CONTROLLER_SECRET=<shared HMAC secret>
SANDBOX_BACKEND=docker
DOCKER_GID=<group id for the Docker socket>
```

Remote production provider configuration:

```text
SANDBOX_PROVIDER_URL=https://sandbox-provider.internal
SANDBOX_PROVIDER_TOKEN=<provider credential>
```

Endpoints are internal-only. `/v1/*` requires an HMAC signature and timestamp. `/health/live` checks the process; `/health/ready` fails closed when the selected sandbox backend is unavailable.
