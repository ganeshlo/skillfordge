import re
import zipfile
from pathlib import Path

from django.conf import settings
from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError


ALLOWED_UPLOADS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def validate_color(value):
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise ValidationError("Use a six-digit hexadecimal color.")
    return value.upper()


def validate_knowledge_upload(upload):
    suffix = Path(upload.name).suffix.lower()
    if suffix not in ALLOWED_UPLOADS:
        raise ValidationError(
            {"file": "Supported files: PDF, DOCX, TXT, Markdown, PPTX, PNG, JPG, and WebP."}
        )
    if upload.size <= 0:
        raise ValidationError({"file": "The uploaded file is empty."})
    if upload.size > settings.KNOWLEDGE_MAX_UPLOAD_BYTES:
        limit_mb = settings.KNOWLEDGE_MAX_UPLOAD_BYTES // (1024 * 1024)
        raise ValidationError({"file": f"File size cannot exceed {limit_mb} MB."})

    try:
        if suffix == ".pdf":
            if upload.read(5) != b"%PDF-":
                raise ValidationError({"file": "The file is not a valid PDF."})
        elif suffix in {".docx", ".pptx"}:
            upload.seek(0)
            with zipfile.ZipFile(upload) as archive:
                names = set(archive.namelist())
                required_prefix = "word/" if suffix == ".docx" else "ppt/"
                if not any(name.startswith(required_prefix) for name in names):
                    raise ValidationError({"file": f"The file is not a valid {suffix[1:].upper()} document."})
        elif suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            upload.seek(0)
            image = Image.open(upload)
            image.verify()
            expected = "JPEG" if suffix in {".jpg", ".jpeg"} else suffix[1:].upper()
            if image.format != expected:
                raise ValidationError({"file": "The image contents do not match its extension."})
        else:
            upload.seek(0)
            upload.read().decode("utf-8")
    except (UnicodeDecodeError, zipfile.BadZipFile, UnidentifiedImageError, OSError) as exc:
        raise ValidationError({"file": "The uploaded file is corrupted or has an invalid format."}) from exc
    finally:
        upload.seek(0)
    return ALLOWED_UPLOADS[suffix]


def validate_folder_parent(*, owner, parent, instance=None):
    if parent is None:
        return
    if parent.owner_id != owner.id:
        raise ValidationError({"parent": "Folder does not belong to your knowledge base."})
    depth = 1
    cursor = parent
    while cursor:
        if instance and cursor.id == instance.id:
            raise ValidationError({"parent": "A folder cannot be moved inside itself."})
        cursor = cursor.parent
        depth += 1
        if depth > 8:
            raise ValidationError({"parent": "Folder hierarchy cannot exceed eight levels."})
