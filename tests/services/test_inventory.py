from datetime import date, timedelta

import pytest

from app.schemas.household_item import HouseholdItemCreate, HouseholdItemUpdate, ItemStatus
from app.services.inventory import InvalidReferenceError, create_item, list_items, set_item_status, update_item
from tests.factories.model_factories import make_category, make_room, make_user


def test_create_item_rejects_unknown_room(db_session):
    user = make_user(db_session)
    category = make_category(db_session)

    payload = HouseholdItemCreate(
        name="Drill",
        room_id=user.id,  # not a real room id
        category_id=category.id,
        user_id=user.id,
    )

    with pytest.raises(InvalidReferenceError):
        create_item(db_session, payload)


def test_create_and_update_item(db_session):
    user = make_user(db_session)
    room = make_room(db_session, name="Garage")
    other_room = make_room(db_session, name="Office")
    category = make_category(db_session, name="Tools")

    item = create_item(
        db_session,
        HouseholdItemCreate(name="Drill", room_id=room.id, category_id=category.id, user_id=user.id),
    )
    assert item.status == "active"

    updated = update_item(db_session, item, HouseholdItemUpdate(room_id=other_room.id))
    assert updated.room_id == other_room.id

    with pytest.raises(InvalidReferenceError):
        update_item(db_session, item, HouseholdItemUpdate(room_id=user.id))


def test_set_item_status(db_session):
    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)

    item = create_item(
        db_session,
        HouseholdItemCreate(name="TV", room_id=room.id, category_id=category.id, user_id=user.id),
    )

    updated = set_item_status(db_session, item, ItemStatus.SOLD)
    assert updated.status == "sold"


def test_list_items_filters_by_room_category_status_and_search(db_session):
    user = make_user(db_session)
    kitchen = make_room(db_session, name="Kitchen")
    office = make_room(db_session, name="Office")
    appliances = make_category(db_session, name="Appliances")
    electronics = make_category(db_session, name="Electronics")

    washer = create_item(
        db_session,
        HouseholdItemCreate(
            name="Washing Machine", room_id=kitchen.id, category_id=appliances.id, user_id=user.id
        ),
    )
    laptop = create_item(
        db_session,
        HouseholdItemCreate(name="Laptop", room_id=office.id, category_id=electronics.id, user_id=user.id),
    )
    set_item_status(db_session, laptop, ItemStatus.SOLD)

    assert [item.id for item in list_items(db_session, room_id=kitchen.id)] == [washer.id]
    assert [item.id for item in list_items(db_session, category_id=electronics.id)] == [laptop.id]
    assert [item.id for item in list_items(db_session, status=ItemStatus.SOLD)] == [laptop.id]
    assert [item.id for item in list_items(db_session, search="wash")] == [washer.id]
    assert list_items(db_session, search="nonexistent") == []


def test_list_items_filters_by_warranty_status(db_session):
    from app.db.models import Warranty

    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)

    with_expired = create_item(
        db_session,
        HouseholdItemCreate(name="Fridge", room_id=room.id, category_id=category.id, user_id=user.id),
    )
    with_expired.warranty = Warranty(expires_on=date.today() - timedelta(days=1), provider="Acme")

    with_active = create_item(
        db_session,
        HouseholdItemCreate(name="Oven", room_id=room.id, category_id=category.id, user_id=user.id),
    )
    with_active.warranty = Warranty(expires_on=date.today() + timedelta(days=30), provider="Acme")

    without_warranty = create_item(
        db_session,
        HouseholdItemCreate(name="Kettle", room_id=room.id, category_id=category.id, user_id=user.id),
    )
    db_session.commit()

    assert [i.id for i in list_items(db_session, warranty_status="expired")] == [with_expired.id]
    assert [i.id for i in list_items(db_session, warranty_status="active")] == [with_active.id]
    assert [i.id for i in list_items(db_session, warranty_status="none")] == [without_warranty.id]
