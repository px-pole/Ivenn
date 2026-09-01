from datetime import date, timedelta

import pytest

from app.schemas.household_item import HouseholdItemCreate
from app.schemas.warranty import WarrantyCreate, WarrantyUpdate
from app.services.inventory import create_item
from app.services.warranty import (
    ItemNotFoundError,
    WarrantyAlreadyExistsError,
    create_warranty,
    delete_warranty,
    get_warranty,
    list_expiring_within,
    update_warranty,
)
from tests.factories.model_factories import make_category, make_room, make_user


def _make_item(db_session, name="Fridge"):
    user = make_user(db_session, email=f"{name.lower()}@example.com")
    room = make_room(db_session, name=f"{name}-room")
    category = make_category(db_session, name=f"{name}-category")
    return create_item(
        db_session,
        HouseholdItemCreate(name=name, room_id=room.id, category_id=category.id, user_id=user.id),
    )


def test_create_and_get_warranty(db_session):
    item = _make_item(db_session)

    warranty = create_warranty(
        db_session, item.id, WarrantyCreate(provider="Acme", expires_on=date.today() + timedelta(days=10))
    )

    assert get_warranty(db_session, item.id).id == warranty.id


def test_create_warranty_rejects_unknown_item(db_session):
    import uuid

    with pytest.raises(ItemNotFoundError):
        create_warranty(db_session, uuid.uuid4(), WarrantyCreate(expires_on=date.today()))


def test_create_warranty_rejects_duplicate(db_session):
    item = _make_item(db_session)
    create_warranty(db_session, item.id, WarrantyCreate(expires_on=date.today()))

    with pytest.raises(WarrantyAlreadyExistsError):
        create_warranty(db_session, item.id, WarrantyCreate(expires_on=date.today()))


def test_update_and_delete_warranty(db_session):
    item = _make_item(db_session)
    warranty = create_warranty(db_session, item.id, WarrantyCreate(expires_on=date.today()))

    updated = update_warranty(db_session, warranty, WarrantyUpdate(provider="NewCo"))
    assert updated.provider == "NewCo"

    delete_warranty(db_session, warranty)
    assert get_warranty(db_session, item.id) is None


def test_list_expiring_within_filters_by_horizon_and_status(db_session):
    from app.schemas.household_item import ItemStatus
    from app.services.inventory import set_item_status

    soon = _make_item(db_session, name="Oven")
    create_warranty(db_session, soon.id, WarrantyCreate(expires_on=date.today() + timedelta(days=20)))

    far_out = _make_item(db_session, name="Boiler")
    create_warranty(db_session, far_out.id, WarrantyCreate(expires_on=date.today() + timedelta(days=200)))

    already_expired = _make_item(db_session, name="Toaster")
    create_warranty(db_session, already_expired.id, WarrantyCreate(expires_on=date.today() - timedelta(days=5)))

    sold_item = _make_item(db_session, name="Laptop")
    create_warranty(db_session, sold_item.id, WarrantyCreate(expires_on=date.today() + timedelta(days=15)))
    set_item_status(db_session, sold_item, ItemStatus.SOLD)

    results = list_expiring_within(db_session, 30)
    assert [w.item_id for w in results] == [soon.id]
