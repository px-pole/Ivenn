import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage import delete_file, save_file
from app.db.models import Attachment, HouseholdItem
from app.schemas.attachment import AttachmentType


class ItemNotFoundError(Exception):
    """Raised when the parent household item does not exist."""


def create_attachment(
    db: Session,
    *,
    item_id: uuid.UUID,
    attachment_type: AttachmentType,
    original_filename: str,
    mime_type: str,
    content: bytes,
) -> Attachment:
    item = db.get(HouseholdItem, item_id)
    if item is None:
        raise ItemNotFoundError(f"Item {item_id} does not exist")

    storage_key = save_file(content=content, original_filename=original_filename, mime_type=mime_type)

    attachment = Attachment(
        item_id=item_id,
        storage_key=storage_key,
        file_name=original_filename[:255],
        mime_type=mime_type,
        attachment_type=attachment_type.value,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def list_attachments(db: Session, item_id: uuid.UUID) -> list[Attachment]:
    stmt = select(Attachment).where(Attachment.item_id == item_id).order_by(Attachment.file_name)
    return list(db.scalars(stmt))


def get_attachment(db: Session, item_id: uuid.UUID, attachment_id: uuid.UUID) -> Attachment | None:
    stmt = select(Attachment).where(Attachment.id == attachment_id, Attachment.item_id == item_id)
    return db.scalars(stmt).first()


def delete_attachment(db: Session, attachment: Attachment) -> None:
    delete_file(attachment.storage_key)
    db.delete(attachment)
    db.commit()
