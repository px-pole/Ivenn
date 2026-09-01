import pytest

from app.schemas.attachment import AttachmentType
from app.services.attachments import (
    ItemNotFoundError,
    create_attachment,
    delete_attachment,
    get_attachment,
    list_attachments,
)
from tests.factories.model_factories import make_category, make_room, make_user
from app.schemas.household_item import HouseholdItemCreate
from app.services.inventory import create_item


def _make_item(db_session):
    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)
    return create_item(
        db_session,
        HouseholdItemCreate(name="Washing Machine", room_id=room.id, category_id=category.id, user_id=user.id),
    )


def test_create_attachment_links_to_item(db_session, storage_dir):
    item = _make_item(db_session)

    attachment = create_attachment(
        db_session,
        item_id=item.id,
        attachment_type=AttachmentType.RECEIPT,
        original_filename="receipt.pdf",
        mime_type="application/pdf",
        content=b"receipt-bytes",
    )

    assert attachment.item_id == item.id
    assert attachment.attachment_type == "receipt"
    assert [a.id for a in list_attachments(db_session, item.id)] == [attachment.id]


def test_create_attachment_rejects_unknown_item(db_session, storage_dir):
    with pytest.raises(ItemNotFoundError):
        create_attachment(
            db_session,
            item_id=__import__("uuid").uuid4(),
            attachment_type=AttachmentType.OTHER,
            original_filename="a.png",
            mime_type="image/png",
            content=b"data",
        )


def test_delete_attachment_removes_record_and_file(db_session, storage_dir):
    from app.core.storage import resolve_path

    item = _make_item(db_session)
    attachment = create_attachment(
        db_session,
        item_id=item.id,
        attachment_type=AttachmentType.ITEM_PHOTO,
        original_filename="photo.jpg",
        mime_type="image/jpeg",
        content=b"photo-bytes",
    )
    stored_path = resolve_path(attachment.storage_key)
    assert stored_path.exists()

    delete_attachment(db_session, attachment)

    assert not stored_path.exists()
    assert get_attachment(db_session, item.id, attachment.id) is None
