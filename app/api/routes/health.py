import shutil

from fastapi import APIRouter

from app.core.storage import ALLOWED_MIME_TYPES, MAX_UPLOAD_SIZE_BYTES

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/capabilities")
def capabilities() -> dict[str, object]:
    return {
        "api_version": "v1",
        "attachments": {
            "max_upload_size_bytes": MAX_UPLOAD_SIZE_BYTES,
            "mime_types": sorted(ALLOWED_MIME_TYPES),
        },
        "receipt_extraction": {
            "available": shutil.which("tesseract") is not None,
            "mime_types": ["image/jpeg", "image/png", "image/webp"],
            "applies_automatically": False,
        },
    }
