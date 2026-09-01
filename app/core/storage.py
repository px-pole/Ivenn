import mimetypes
import uuid
from pathlib import Path

from app.core.config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class UnsupportedFileTypeError(Exception):
    """Raised when an uploaded file's MIME type is not allowed."""


class FileTooLargeError(Exception):
    """Raised when an uploaded file exceeds the maximum allowed size."""


def _safe_extension(mime_type: str, original_filename: str) -> str:
    guessed = mimetypes.guess_extension(mime_type)
    if guessed:
        return guessed

    suffix = Path(original_filename).suffix
    if 0 < len(suffix) <= 10 and all(c.isalnum() for c in suffix[1:]):
        return suffix
    return ""


def save_file(*, content: bytes, original_filename: str, mime_type: str) -> str:
    """Validate and persist an uploaded file, returning its server-generated storage key.

    The storage key is always generated server-side; the client-supplied filename
    is never used to build a filesystem path, which avoids path traversal.
    """
    if mime_type not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileTypeError(f"Unsupported file type: {mime_type}")
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLargeError("File exceeds the maximum allowed size of 10 MB")

    storage_dir = Path(settings.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    storage_key = f"{uuid.uuid4()}{_safe_extension(mime_type, original_filename)}"
    (storage_dir / storage_key).write_bytes(content)
    return storage_key


def delete_file(storage_key: str) -> None:
    Path(settings.storage_dir, storage_key).unlink(missing_ok=True)


def resolve_path(storage_key: str) -> Path:
    return Path(settings.storage_dir, storage_key)
