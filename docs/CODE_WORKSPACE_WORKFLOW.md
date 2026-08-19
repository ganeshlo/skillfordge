# Code workspace workflow

## User workflow

1. Open **Code workspace** and create a project from a language template.
2. Create or select a file in the explorer. Files are owner-scoped by the API.
3. Edit in Monaco. Changes autosave after 60 seconds and each changed save creates a revision.
4. Use **Versions** to inspect revision metadata or **Download** to export the project as a ZIP.
5. For a server language, optionally enter standard input and select **Run**. For HTML, CSS, or React, select **Preview**.
6. While a job is active, **Run** becomes **Stop**. The output panel shows status, stdout, stderr, exit code, duration, and memory.

## Workspace controls

- Drag the Explorer's right edge to resize it, or use its minimize/maximize controls.
- Drag the Terminal's top edge to resize it vertically, or minimize/maximize it from the Terminal header.
- Collapse or expand the dashboard navigation with the desktop sidebar control.
- Right-click inside Monaco for LearnOS actions: Run/Preview, Save, New File, Versions, Download, panel toggles, and Delete File.
- Keyboard shortcuts: `Cmd/Ctrl+Enter` runs, `Cmd/Ctrl+S` saves, `Cmd/Ctrl+J` toggles Terminal, and `Cmd/Ctrl+Shift+E` toggles Explorer.

## Save lifecycle

```text
Monaco edit
  -> local unsaved state
  -> debounced PATCH /api/v1/coding/files/{id}/
  -> owner and size validation
  -> file update + checksum
  -> immutable ProjectFileRevision
  -> saved state in the editor
```

## Secure execution lifecycle

```text
Run
  -> save latest source
  -> POST /api/v1/coding/executions/ + Idempotency-Key
  -> authenticate user and verify file ownership
  -> validate the language allowlist, source, stdin, and server-owned limits
  -> snapshot source into ExecutionJob
  -> Celery dispatch task
  -> HMAC-signed request to execution controller
  -> selected sandbox backend
  -> temporary restricted language container
  -> bounded stdout/stderr and execution metrics
  -> controller status polling
  -> Django job polling
  -> editor output panel
```

Execution jobs move through `queued`, `dispatching`, `running`, and one terminal state: `succeeded`, `failed`, `cancelled`, or `timed_out`.

## Security boundary

Server-side user code is never evaluated in React, Django, Celery, or the execution controller process. The controller creates an ephemeral local Docker sandbox or delegates to a remote hardened provider. HTML/CSS/React previews run separately in an iframe without same-origin access. The API enforces a language allowlist, network-disabled jobs, CPU and memory limits, execution timeouts, bounded input/output, owner isolation, audit logs, and idempotent submission.

The system intentionally fails closed. When `EXECUTION_CONTROLLER_URL` or `EXECUTION_CONTROLLER_SECRET` is absent, Django reports execution as unavailable. When the controller cannot reach its selected sandbox backend, its readiness endpoint returns HTTP 503. The editor remains available for project and file management.
