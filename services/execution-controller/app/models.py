from typing import Literal
from pydantic import BaseModel, Field, field_validator

MAX_SOURCE_BYTES = 512 * 1024
MAX_STDIN_BYTES = 16 * 1024


class ExecutionLimits(BaseModel):
    timeout_seconds: int = Field(ge=1, le=30)
    memory_mb: int = Field(ge=32, le=768)
    cpu_millis: int = Field(ge=100, le=1000)
    output_bytes: int = Field(ge=1024, le=131072)
    network: Literal[False]


class ExecutionRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=128)
    language: Literal[
        "python", "javascript", "typescript", "java", "c", "cpp", "go", "rust",
        "php", "ruby", "kotlin", "sql",
    ]
    source: str
    stdin: str = ""
    limits: ExecutionLimits

    @field_validator("source")
    @classmethod
    def source_size(cls, value):
        if len(value.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise ValueError("source exceeds the maximum size")
        return value

    @field_validator("stdin")
    @classmethod
    def stdin_size(cls, value):
        if len(value.encode("utf-8")) > MAX_STDIN_BYTES:
            raise ValueError("stdin exceeds the maximum size")
        return value


class ExecutionAccepted(BaseModel):
    id: str
    status: Literal["queued", "running"]


class ExecutionResult(BaseModel):
    id: str
    status: Literal["queued", "running", "succeeded", "failed", "cancelled", "timed_out"]
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    runtime_ms: int | None = None
    memory_bytes: int | None = None
