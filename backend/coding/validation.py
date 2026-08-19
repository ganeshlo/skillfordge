from pathlib import PurePosixPath
from rest_framework.exceptions import ValidationError

MAX_FILE_BYTES = 512 * 1024
MAX_FILES_PER_PROJECT = 200
ALLOWED_LANGUAGES = {
    "python", "javascript", "typescript", "java", "c", "cpp", "go", "rust", "php", "ruby",
    "kotlin", "sql", "html", "css", "react", "json", "markdown", "plaintext",
}
RUNNABLE_LANGUAGES = {
    "python", "javascript", "typescript", "java", "c", "cpp", "go", "rust",
    "php", "ruby", "kotlin", "sql",
}
MAX_STDIN_BYTES = 16 * 1024


def validate_project_path(value):
    if not value or "\x00" in value or "\\" in value or value.startswith("/"):
        raise ValidationError("Use a non-empty project-relative POSIX path.")
    path = PurePosixPath(value)
    if ".." in path.parts or "." in path.parts or len(path.parts) > 20:
        raise ValidationError("The file path contains a disallowed segment.")
    normalized = str(path)
    if len(normalized) > 500:
        raise ValidationError("The file path is too long.")
    return normalized


def validate_content(value):
    if len(value.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValidationError(f"Each file is limited to {MAX_FILE_BYTES // 1024} KB.")
    return value


def validate_stdin(value):
    if len(value.encode("utf-8")) > MAX_STDIN_BYTES:
        raise ValidationError(f"Standard input is limited to {MAX_STDIN_BYTES // 1024} KB.")
    return value
