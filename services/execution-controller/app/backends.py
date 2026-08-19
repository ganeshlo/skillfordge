import asyncio
import io
import logging
import os
import tarfile
import threading
import time
from abc import ABC, abstractmethod

import docker
import httpx
from docker.errors import DockerException, ImageNotFound

from .models import ExecutionAccepted, ExecutionRequest, ExecutionResult

logger = logging.getLogger(__name__)

SQL_RUNNER = """import sqlite3
database = sqlite3.connect(\":memory:\")
script = open(\"/workspace/main.sql\", encoding=\"utf-8\").read()
for part in script.split(\";\"):
    statement = part.strip()
    if not statement:
        continue
    cursor = database.execute(statement)
    if cursor.description:
        print(\" | \".join(column[0] for column in cursor.description))
        for row in cursor.fetchall():
            print(\" | \".join(\"NULL\" if value is None else str(value) for value in row))
database.commit()
"""


class BackendUnavailable(RuntimeError):
    pass


class SandboxBackend(ABC):
    @property
    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    async def submit(self, execution: ExecutionRequest) -> ExecutionAccepted: ...

    @abstractmethod
    async def status(self, execution_id: str) -> ExecutionResult: ...

    @abstractmethod
    async def cancel(self, execution_id: str) -> ExecutionResult: ...


class DisabledBackend(SandboxBackend):
    @property
    def available(self):
        return False

    async def submit(self, execution):
        raise BackendUnavailable("No isolated sandbox backend is configured")

    async def status(self, execution_id):
        raise BackendUnavailable("No isolated sandbox backend is configured")

    async def cancel(self, execution_id):
        raise BackendUnavailable("No isolated sandbox backend is configured")


class DockerSandboxBackend(SandboxBackend):
    """Runs each job in a short-lived, resource-limited Docker container."""

    images = {
        "python": os.getenv("PYTHON_RUNNER_IMAGE", "python:3.12-alpine"),
        "javascript": os.getenv("JAVASCRIPT_RUNNER_IMAGE", "node:22-alpine"),
        "typescript": os.getenv("TYPESCRIPT_RUNNER_IMAGE", "denoland/deno:alpine"),
        "java": os.getenv("JAVA_RUNNER_IMAGE", "eclipse-temurin:21-jdk-alpine"),
        "c": os.getenv("C_RUNNER_IMAGE", "gcc:14"),
        "cpp": os.getenv("CPP_RUNNER_IMAGE", "gcc:14"),
        "go": os.getenv("GO_RUNNER_IMAGE", "golang:1.24-alpine"),
        "rust": os.getenv("RUST_RUNNER_IMAGE", "rust:alpine"),
        "php": os.getenv("PHP_RUNNER_IMAGE", "php:8.4-cli-alpine"),
        "ruby": os.getenv("RUBY_RUNNER_IMAGE", "ruby:alpine"),
        "kotlin": os.getenv("KOTLIN_RUNNER_IMAGE", "learnos-kotlin-runner:2.1.20"),
        "sql": os.getenv("SQL_RUNNER_IMAGE", "python:3.12-alpine"),
    }
    commands = {
        "python": ["sh", "-c", "python -B /workspace/main.py < /workspace/stdin.txt"],
        "javascript": ["sh", "-c", "node /workspace/main.js < /workspace/stdin.txt"],
        "typescript": ["sh", "-c", "deno run --no-prompt --no-config /workspace/main.ts < /workspace/stdin.txt"],
        "java": ["sh", "-c", "javac -d /tmp/classes /workspace/Main.java && java -cp /tmp/classes Main < /workspace/stdin.txt"],
        "c": ["sh", "-c", "gcc -O2 -Wall -Wextra /workspace/main.c -o /tmp/main && /tmp/main < /workspace/stdin.txt"],
        "cpp": ["sh", "-c", "g++ -O2 -Wall -Wextra /workspace/main.cpp -o /tmp/main && /tmp/main < /workspace/stdin.txt"],
        "go": ["sh", "-c", "GOCACHE=/tmp/go-cache go run /workspace/main.go < /workspace/stdin.txt"],
        "rust": ["sh", "-c", "rustc /workspace/main.rs -o /tmp/main && /tmp/main < /workspace/stdin.txt"],
        "php": ["sh", "-c", "php /workspace/main.php < /workspace/stdin.txt"],
        "ruby": ["sh", "-c", "ruby /workspace/main.rb < /workspace/stdin.txt"],
        "kotlin": ["sh", "-c", "kotlinc /workspace/Main.kt -include-runtime -d /tmp/main.jar && java -jar /tmp/main.jar < /workspace/stdin.txt"],
        "sql": ["sh", "-c", "python -B /workspace/sql_runner.py < /workspace/stdin.txt"],
    }
    filenames = {
        "python": "main.py", "javascript": "main.js", "typescript": "main.ts",
        "java": "Main.java", "c": "main.c", "cpp": "main.cpp", "go": "main.go",
        "rust": "main.rs", "php": "main.php", "ruby": "main.rb", "kotlin": "Main.kt",
        "sql": "main.sql",
    }

    def __init__(self):
        self.client = docker.from_env(timeout=5)
        self.results: dict[str, ExecutionResult] = {}
        self.containers: dict[str, str] = {}
        self.lock = threading.Lock()

    @property
    def available(self):
        try:
            return bool(self.client.ping())
        except DockerException:
            return False

    async def submit(self, execution):
        with self.lock:
            existing = self.results.get(execution.request_id)
            if existing:
                return ExecutionAccepted(id=existing.id, status="running" if existing.status == "running" else "queued")
            self.results[execution.request_id] = ExecutionResult(id=execution.request_id, status="queued")
        asyncio.create_task(asyncio.to_thread(self._execute, execution))
        return ExecutionAccepted(id=execution.request_id, status="queued")

    async def status(self, execution_id):
        with self.lock:
            result = self.results.get(execution_id)
        if not result:
            raise BackendUnavailable("Execution job was not found by this controller")
        return result

    async def cancel(self, execution_id):
        with self.lock:
            result = self.results.get(execution_id)
            container_id = self.containers.get(execution_id)
        if not result:
            raise BackendUnavailable("Execution job was not found by this controller")
        if result.status in {"succeeded", "failed", "cancelled", "timed_out"}:
            return result
        if container_id:
            try:
                self.client.containers.get(container_id).kill()
            except DockerException:
                pass
        cancelled = result.model_copy(update={"status": "cancelled"})
        self._store(cancelled)
        return cancelled

    def _store(self, result):
        with self.lock:
            self.results[result.id] = result

    @staticmethod
    def _archive(execution):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w") as archive:
            for name, content in (
                (DockerSandboxBackend.filenames[execution.language], execution.source),
                ("stdin.txt", execution.stdin),
            ):
                encoded = content.encode("utf-8")
                info = tarfile.TarInfo(name)
                info.size = len(encoded)
                info.mode = 0o400
                info.uid = info.gid = 65534
                archive.addfile(info, io.BytesIO(encoded))
            if execution.language == "sql":
                encoded = SQL_RUNNER.encode("utf-8")
                info = tarfile.TarInfo("sql_runner.py")
                info.size = len(encoded)
                info.mode = 0o400
                info.uid = info.gid = 65534
                archive.addfile(info, io.BytesIO(encoded))
        output.seek(0)
        return output

    @staticmethod
    def _bounded(stdout, stderr, limit):
        stdout = stdout[:limit]
        stderr = stderr[: max(0, limit - len(stdout))]
        return stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    def _execute(self, execution):
        started = time.monotonic()
        container = None
        loader = None
        volume = None
        try:
            image = self.images[execution.language]
            try:
                self.client.images.get(image)
            except ImageNotFound:
                self.client.images.pull(image)
            volume = self.client.volumes.create(labels={"learnos.execution": execution.request_id})
            loader = self.client.containers.create(
                image=image,
                entrypoint=[],
                command=["sh", "-c", "sleep 30"],
                network_mode="none",
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                volumes={volume.name: {"bind": "/workspace", "mode": "rw"}},
            )
            loader.start()
            loader.put_archive("/workspace", self._archive(execution))
            loader.remove(force=True)
            loader = None
            container = self.client.containers.create(
                image=image,
                entrypoint=[],
                command=self.commands[execution.language],
                name=f"learnos-job-{execution.request_id}",
                network_mode="none",
                read_only=True,
                user="65534:65534",
                working_dir="/workspace",
                mem_limit=f"{execution.limits.memory_mb}m",
                memswap_limit=f"{execution.limits.memory_mb}m",
                nano_cpus=execution.limits.cpu_millis * 1_000_000,
                pids_limit=64,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                environment={"HOME": "/tmp", "JAVA_TOOL_OPTIONS": "-Xmx512m -XX:MaxMetaspaceSize=128m"},
                tmpfs={"/tmp": "rw,exec,nosuid,nodev,size=128m,mode=1777"},
                labels={"learnos.execution": execution.request_id},
                volumes={volume.name: {"bind": "/workspace", "mode": "ro"}},
            )
            with self.lock:
                self.containers[execution.request_id] = container.id
                if self.results[execution.request_id].status == "cancelled":
                    return
            self._store(ExecutionResult(id=execution.request_id, status="running"))
            container.start()
            deadline = time.monotonic() + execution.limits.timeout_seconds
            timed_out = False
            while time.monotonic() < deadline:
                container.reload()
                if container.status in {"exited", "dead"}:
                    break
                time.sleep(0.05)
            else:
                timed_out = True
                container.kill()
            result = container.wait(timeout=3)
            stdout, stderr = self._bounded(
                container.logs(stdout=True, stderr=False),
                container.logs(stdout=False, stderr=True),
                execution.limits.output_bytes,
            )
            exit_code = result.get("StatusCode")
            status_value = "timed_out" if timed_out else "succeeded" if exit_code == 0 else "failed"
            with self.lock:
                cancelled = self.results[execution.request_id].status == "cancelled"
            if not cancelled:
                self._store(ExecutionResult(
                    id=execution.request_id,
                    status=status_value,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    runtime_ms=int((time.monotonic() - started) * 1000),
                ))
        except (DockerException, KeyError, OSError, ValueError) as exc:
            logger.exception("Isolated Docker execution failed", extra={"execution_id": execution.request_id})
            with self.lock:
                cancelled = self.results[execution.request_id].status == "cancelled"
            if not cancelled:
                self._store(ExecutionResult(
                    id=execution.request_id,
                    status="failed",
                    stderr=f"The isolated runner failed to start: {type(exc).__name__}",
                    runtime_ms=int((time.monotonic() - started) * 1000),
                ))
        finally:
            if loader:
                try:
                    loader.remove(force=True)
                except DockerException:
                    pass
            if container:
                try:
                    container.remove(force=True)
                except DockerException:
                    pass
            if volume:
                try:
                    volume.remove(force=True)
                except DockerException:
                    pass
            with self.lock:
                self.containers.pop(execution.request_id, None)


class RemoteSandboxBackend(SandboxBackend):
    """Adapter for a hardened sandbox provider; never runs source in this process."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    @property
    def available(self):
        return bool(self.base_url and self.token)

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @staticmethod
    def _translate_failure(exc: Exception):
        raise BackendUnavailable("The isolated sandbox provider is unavailable or returned an invalid response") from exc

    async def submit(self, execution):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.base_url}/jobs", json=execution.model_dump(), headers=self._headers())
                response.raise_for_status()
                return ExecutionAccepted.model_validate(response.json())
        except (httpx.HTTPError, ValueError) as exc:
            self._translate_failure(exc)

    async def status(self, execution_id):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/jobs/{execution_id}", headers=self._headers())
                response.raise_for_status()
                return ExecutionResult.model_validate(response.json())
        except (httpx.HTTPError, ValueError) as exc:
            self._translate_failure(exc)

    async def cancel(self, execution_id):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(f"{self.base_url}/jobs/{execution_id}/cancel", headers=self._headers())
                response.raise_for_status()
                return ExecutionResult.model_validate(response.json())
        except (httpx.HTTPError, ValueError) as exc:
            self._translate_failure(exc)
