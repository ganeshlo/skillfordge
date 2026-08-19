import hashlib
import hmac
import json
import time
import pytest
from fastapi.testclient import TestClient

from app.backends import SandboxBackend
from app.main import create_app
from app.models import ExecutionAccepted, ExecutionResult

SECRET = "controller-test-secret-with-enough-entropy"


class FakeBackend(SandboxBackend):
    @property
    def available(self): return True

    async def submit(self, execution):
        return ExecutionAccepted(id=execution.request_id, status="queued")

    async def status(self, execution_id):
        return ExecutionResult(id=execution_id, status="succeeded", stdout="ok\n", exit_code=0, runtime_ms=4, memory_bytes=1024)

    async def cancel(self, execution_id):
        return ExecutionResult(id=execution_id, status="cancelled")


def headers(method, path, body=""):
    timestamp = str(int(time.time()))
    signature = hmac.new(SECRET.encode(), f"{timestamp}.{method}.{path}.{body}".encode(), hashlib.sha256).hexdigest()
    return {"X-LearnOS-Timestamp": timestamp, "X-LearnOS-Signature": signature, "Content-Type": "application/json"}


def payload():
    return {
        "request_id": "execution-request-123",
        "language": "python",
        "source": "print('ok')",
        "stdin": "",
        "limits": {"timeout_seconds": 10, "memory_mb": 128, "cpu_millis": 500, "output_bytes": 65536, "network": False},
    }


def test_rejects_unsigned_request():
    client = TestClient(create_app(FakeBackend(), SECRET))
    assert client.post("/v1/executions", json=payload()).status_code == 401


def test_accepts_signed_bounded_job_and_returns_result():
    client = TestClient(create_app(FakeBackend(), SECRET))
    body = json.dumps(payload(), separators=(",", ":"), sort_keys=True)
    accepted = client.post("/v1/executions", content=body, headers=headers("POST", "/v1/executions", body))
    assert accepted.status_code == 202
    job_id = accepted.json()["id"]
    result = client.get(f"/v1/executions/{job_id}", headers=headers("GET", f"/v1/executions/{job_id}"))
    assert result.json()["stdout"] == "ok\n"


def test_rejects_network_and_excessive_limits():
    client = TestClient(create_app(FakeBackend(), SECRET))
    invalid = payload()
    invalid["limits"]["network"] = True
    invalid["limits"]["memory_mb"] = 2048
    body = json.dumps(invalid, separators=(",", ":"), sort_keys=True)
    assert client.post("/v1/executions", content=body, headers=headers("POST", "/v1/executions", body)).status_code == 422


@pytest.mark.parametrize("language", [
    "python", "javascript", "typescript", "java", "c", "cpp", "go", "rust",
    "php", "ruby", "kotlin", "sql",
])
def test_accepts_each_server_execution_language(language):
    client = TestClient(create_app(FakeBackend(), SECRET))
    request_payload = payload()
    request_payload["language"] = language
    body = json.dumps(request_payload, separators=(",", ":"), sort_keys=True)
    response = client.post("/v1/executions", content=body, headers=headers("POST", "/v1/executions", body))
    assert response.status_code == 202
