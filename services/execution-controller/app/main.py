import os
from fastapi import FastAPI, HTTPException, Request, status

from .auth import verify_request
from .backends import BackendUnavailable, DisabledBackend, DockerSandboxBackend, RemoteSandboxBackend, SandboxBackend
from .models import ExecutionAccepted, ExecutionRequest, ExecutionResult


def configured_backend():
    if os.getenv("SANDBOX_BACKEND", "").lower() == "docker":
        return DockerSandboxBackend()
    provider_url = os.getenv("SANDBOX_PROVIDER_URL", "")
    provider_token = os.getenv("SANDBOX_PROVIDER_TOKEN", "")
    return RemoteSandboxBackend(provider_url, provider_token) if provider_url and provider_token else DisabledBackend()


def create_app(backend: SandboxBackend | None = None, signing_secret: str | None = None):
    application = FastAPI(title="LearnOS Execution Controller", version="1.0.0", docs_url=None, redoc_url=None)
    application.state.backend = backend or configured_backend()
    application.state.signing_secret = signing_secret if signing_secret is not None else os.getenv("EXECUTION_CONTROLLER_SECRET", "")

    @application.get("/health/live")
    async def live():
        return {"status": "ok", "service": "execution-controller"}

    @application.get("/health/ready")
    async def ready():
        if not application.state.backend.available:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Sandbox backend is not configured")
        return {"status": "ready", "sandbox_backend": "available"}

    @application.post("/v1/executions", response_model=ExecutionAccepted, status_code=202)
    async def submit(execution: ExecutionRequest, request: Request):
        await verify_request(request, application.state.signing_secret)
        try:
            return await application.state.backend.submit(execution)
        except BackendUnavailable as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    @application.get("/v1/executions/{execution_id}", response_model=ExecutionResult)
    async def execution_status(execution_id: str, request: Request):
        await verify_request(request, application.state.signing_secret)
        try:
            return await application.state.backend.status(execution_id)
        except BackendUnavailable as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    @application.post("/v1/executions/{execution_id}/cancel", response_model=ExecutionResult)
    async def cancel(execution_id: str, request: Request):
        await verify_request(request, application.state.signing_secret)
        try:
            return await application.state.backend.cancel(execution_id)
        except BackendUnavailable as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    return application


app = create_app()
