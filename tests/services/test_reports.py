from decimal import Decimal

from app.schemas.household_item import HouseholdItemCreate, HouseholdItemUpdate
from app.services.attachments import create_attachment
from app.services.inventory import create_item, update_item
from app.services.reports import build_room_sections, render_inventory_csv, render_inventory_pdf, total_estimated_value
from app.schemas.attachment import AttachmentType
from tests.factories.model_factories import make_category, make_room, make_user


def test_build_room_sections_groups_by_room_and_sums_values(db_session):
    user = make_user(db_session)
    kitchen = make_room(db_session, name="Kitchen")
    office = make_room(db_session, name="Office")
    appliances = make_category(db_session, name="Appliances")
    electronics = make_category(db_session, name="Electronics")

    washer = create_item(
        db_session,
        HouseholdItemCreate(name="Washer", room_id=kitchen.id, category_id=appliances.id, user_id=user.id),
    )
    update_item(db_session, washer, HouseholdItemUpdate(estimated_value=Decimal("450.00")))

    fridge = create_item(
        db_session,
        HouseholdItemCreate(name="Fridge", room_id=kitchen.id, category_id=appliances.id, user_id=user.id),
    )
    update_item(db_session, fridge, HouseholdItemUpdate(estimated_value=Decimal("300.00")))

    laptop = create_item(
        db_session,
        HouseholdItemCreate(name="Laptop", room_id=office.id, category_id=electronics.id, user_id=user.id),
    )
    update_item(db_session, laptop, HouseholdItemUpdate(estimated_value=Decimal("999.99")))

    sections = build_room_sections(db_session)

    assert [s.room_name for s in sections] == ["Kitchen", "Office"]
    kitchen_section = sections[0]
    assert {row.item.name for row in kitchen_section.rows} == {"Washer", "Fridge"}
    assert kitchen_section.subtotal == Decimal("750.00")
    assert total_estimated_value(sections) == Decimal("1749.99")


def test_build_room_sections_excludes_non_active_items_by_default(db_session):
    from app.schemas.household_item import ItemStatus
    from app.services.inventory import set_item_status

    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)

    kept = create_item(
        db_session, HouseholdItemCreate(name="Kept", room_id=room.id, category_id=category.id, user_id=user.id)
    )
    sold = create_item(
        db_session, HouseholdItemCreate(name="Sold", room_id=room.id, category_id=category.id, user_id=user.id)
    )
    set_item_status(db_session, sold, ItemStatus.SOLD)

    sections = build_room_sections(db_session)
    names = {row.item.name for section in sections for row in section.rows}
    assert names == {"Kept"}


def test_render_inventory_csv_contains_item_rows(db_session):
    user = make_user(db_session)
    room = make_room(db_session, name="Garage")
    category = make_category(db_session, name="Tools")
    create_item(
        db_session,
        HouseholdItemCreate(
            name="Drill", room_id=room.id, category_id=category.id, user_id=user.id, serial_number="SN-1"
        ),
    )

    sections = build_room_sections(db_session)
    csv_text = render_inventory_csv(sections)

    assert "Garage" in csv_text
    assert "Drill" in csv_text
    assert "SN-1" in csv_text


def test_render_inventory_pdf_produces_pdf_bytes(db_session, storage_dir):
    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)
    item = create_item(
        db_session, HouseholdItemCreate(name="TV", room_id=room.id, category_id=category.id, user_id=user.id)
    )
    create_attachment(
        db_session,
        item_id=item.id,
        attachment_type=AttachmentType.ITEM_PHOTO,
        original_filename="tv.jpg",
        mime_type="image/jpeg",
        content=b"fake-image-bytes",
    )

    sections = build_room_sections(db_session)
    pdf_bytes = render_inventory_pdf(sections)

    assert pdf_bytes.startswith(b"%PDF-")
