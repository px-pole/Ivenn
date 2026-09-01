from datetime import date, timedelta

from app.schemas.household_item import HouseholdItemCreate
from app.schemas.warranty import WarrantyCreate
from app.services.inventory import create_item
from app.services.notifications import list_notifications, mark_all_read, sync_warranty_notifications, update_notification
from app.services.warranty import create_warranty, delete_warranty, get_warranty
from tests.factories.model_factories import make_category, make_room, make_user


def _make_item_with_warranty(db_session, name: str, days_until_expiry: int, user=None):
    user = user or make_user(db_session, email=f"{name.lower()}@example.com")
    room = make_room(db_session, name=f"{name}-room")
    category = make_category(db_session, name=f"{name}-category")
    item = create_item(
        db_session,
        HouseholdItemCreate(name=name, room_id=room.id, category_id=category.id, user_id=user.id),
    )
    create_warranty(
        db_session, item.id, WarrantyCreate(expires_on=date.today() + timedelta(days=days_until_expiry))
    )
    return item, user


def test_sync_creates_one_in_app_notification_per_current_window(db_session):
    item, user = _make_item_with_warranty(db_session, "Oven", 25)

    assert sync_warranty_notifications(db_session, user.id) == 1
    assert sync_warranty_notifications(db_session, user.id) == 0
    notifications = list_notifications(db_session, user.id)
    assert len(notifications) == 1
    assert notifications[0].item_id == item.id
    assert "25 day(s)" in notifications[0].message


def test_sync_ignores_far_future_warranties_and_other_users(db_session):
    _, user = _make_item_with_warranty(db_session, "Fence", 200)
    _make_item_with_warranty(db_session, "Other Oven", 10)

    assert list_notifications(db_session, user.id) == []


def test_read_dismiss_and_mark_all_read_state_persists(db_session):
    _, user = _make_item_with_warranty(db_session, "Oven", 10)
    _make_item_with_warranty(db_session, "Boiler", 40, user=user)
    notifications = list_notifications(db_session, user.id)

    update_notification(db_session, notifications[0], is_read=True, is_dismissed=True)
    assert len(list_notifications(db_session, user.id)) == 1
    assert mark_all_read(db_session, user.id) == 1
    assert all(notification.is_read for notification in list_notifications(db_session, user.id))


def test_deleted_warranty_removes_its_in_app_notification(db_session):
    item, user = _make_item_with_warranty(db_session, "Oven", 10)
    assert len(list_notifications(db_session, user.id)) == 1

    delete_warranty(db_session, get_warranty(db_session, item.id))

    assert list_notifications(db_session, user.id) == []
