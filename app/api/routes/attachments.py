import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.dependencies import CurrentUser, DbSession
from app.core.storage import FileTooLargeError, UnsupportedFileTypeError, resolve_path
from app.schemas.attachment import AttachmentRead, AttachmentType, ReceiptExtractionRead
from app.services.attachments import (
    ItemNotFoundError,
    create_attachment,
    delete_attachment,
    get_attachment,
    list_attachments,
)
from app.services.inventory import get_item
from app.services.receipt_extraction import (
    ExtractionUnavailableError,
    ExtractionUnsupportedError,
    extract_receipt,
)

router = APIRouter(prefix="/items/{item_id}/attachments", tags=["attachments"])


def _ensure_owned_item(db: DbSession, item_id: uuid.UUID, current_user: CurrentUser) -> None:
    if get_item(db, item_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Item not found")


@router.post("", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    item_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    attachment_type: AttachmentType = Form(...),
    file: UploadFile = File(...),
) -> AttachmentRead:
    _ensure_owned_item(db, item_id, current_user)
    content = await file.read()
    try:
        return create_attachment(
            db,
            item_id=item_id,
            attachment_type=attachment_type,
            original_filename=file.filename or "upload",
            mime_type=file.content_type or "application/octet-stream",
            content=content,
        )
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc


@router.get("", response_model=list[AttachmentRead])
def list_attachments_endpoint(item_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> list[AttachmentRead]:
    _ensure_owned_item(db, item_id, current_user)
    return list_attachments(db, item_id)


@router.get("/{attachment_id}", response_class=FileResponse)
def download_attachment_endpoint(
    item_id: uuid.UUID, attachment_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> FileResponse:
    _ensure_owned_item(db, item_id, current_user)
    attachment = get_attachment(db, item_id, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    path = resolve_path(attachment.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Attachment file not found")
    return FileResponse(path, media_type=attachment.mime_type, filename=attachment.file_name)


@router.post("/{attachment_id}/extract", response_model=ReceiptExtractionRead)
def extract_attachment_endpoint(
    item_id: uuid.UUID, attachment_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> ReceiptExtractionRead:
    _ensure_owned_item(db, item_id, current_user)
    attachment = get_attachment(db, item_id, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    try:
        return extract_receipt(resolve_path(attachment.storage_key), attachment.mime_type)
    except ExtractionUnsupportedError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ExtractionUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment_endpoint(
    item_id: uuid.UUID, attachment_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> None:
    _ensure_owned_item(db, item_id, current_user)
    attachment = get_attachment(db, item_id, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    delete_attachment(db, attachment)
