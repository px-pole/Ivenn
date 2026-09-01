from typing import Literal

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import settings
from app.schemas.maintenance import GeneratedFileRead, RestoreStatusRead
from app.services.backup import BackupUnsupportedError, create_backup, get_generated_file, read_restore_status, write_export
from app.services.reports import build_room_sections, render_inventory_csv, render_inventory_pdf

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


def _ensure_local_mode() -> None:
    if settings.require_authentication:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Full local backup is unavailable when authentication is required",
        )


def _response(file_name: str) -> GeneratedFileRead:
    return GeneratedFileRead(file_name=file_name, download_path=f"/maintenance/generated/{file_name}")


@router.post("/backup", response_model=GeneratedFileRead)
def create_backup_endpoint(_current_user: CurrentUser) -> GeneratedFileRead:
    _ensure_local_mode()
    try:
        artifact = create_backup(settings.database_url, settings.storage_dir)
    except BackupUnsupportedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _response(artifact.file_name)


@router.post("/export/{export_format}", response_model=GeneratedFileRead)
def create_export_endpoint(
    export_format: Literal["csv", "pdf"], db: DbSession, _current_user: CurrentUser
) -> GeneratedFileRead:
    _ensure_local_mode()
    sections = build_room_sections(db)
    if export_format == "pdf":
        content = render_inventory_pdf(sections)
    else:
        content = render_inventory_csv(sections).encode("utf-8-sig")
    artifact = write_export(content, settings.storage_dir, export_format)
    return _response(artifact.file_name)


@router.get("/generated/{file_name}", response_class=FileResponse)
def download_generated_file(file_name: str, _current_user: CurrentUser) -> FileResponse:
    _ensure_local_mode()
    path = get_generated_file(settings.storage_dir, file_name)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated file not found")
    media_type = {
        ".csv": "text/csv; charset=utf-8",
        ".pdf": "application/pdf",
        ".zip": "application/zip",
    }.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media_type, filename=file_name)


@router.get("/restore-status", response_model=RestoreStatusRead | None)
def restore_status_endpoint(_current_user: CurrentUser) -> RestoreStatusRead | None:
    _ensure_local_mode()
    status_data = read_restore_status(settings.storage_dir, consume=True)
    return RestoreStatusRead.model_validate(status_data) if status_data else None
