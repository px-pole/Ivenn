from datetime import date, timedelta

from tests.factories.model_factories import make_category, make_room, make_user


def _create_due_warranty(client, db_session, name="Oven", days=10):
    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)
    item = client.post(
        "/items",
        json={"name": name, "room_id": str(room.id), "category_id": str(category.id), "user_id": str(user.id)},
    ).json()
    client.post(
        f"/items/{item['id']}/warranty",
        json={"expires_on": (date.today() + timedelta(days=days)).isoformat()},
    )
    return item


def test_versioned_notification_inbox_read_and_dismiss(client, db_session):
    item = _create_due_warranty(client, db_session)

    response = client.get("/api/v1/notifications")
    assert response.status_code == 200
    notification = response.json()[0]
    assert notification["item_id"] == item["id"]
    assert notification["is_read"] is False

    response = client.patch(f"/api/v1/notifications/{notification['id']}", json={"is_read": True})
    assert response.status_code == 200
    assert response.json()["is_read"] is True

    response = client.patch(f"/api/v1/notifications/{notification['id']}", json={"is_dismissed": True})
    assert response.status_code == 200
    assert client.get("/api/v1/notifications").json() == []


def test_mark_all_notifications_read(client, db_session):
    user = make_user(db_session)
    for index, days in enumerate((10, 40)):
        room = make_room(db_session, name=f"Room {index}")
        category = make_category(db_session, name=f"Category {index}")
        item = client.post(
            "/items",
            json={"name": f"Item {index}", "room_id": str(room.id), "category_id": str(category.id), "user_id": str(user.id)},
        ).json()
        client.post(
            f"/items/{item['id']}/warranty",
            json={"expires_on": (date.today() + timedelta(days=days)).isoformat()},
        )

    assert len(client.get("/api/v1/notifications").json()) == 2
    response = client.post("/api/v1/notifications/mark-all-read")
    assert response.json()["updated_count"] == 2
    assert all(notification["is_read"] for notification in client.get("/api/v1/notifications").json())


def test_notification_update_is_user_scoped(client, db_session):
    assert client.patch(
        "/api/v1/notifications/00000000-0000-0000-0000-000000000000",
        json={"is_read": True},
    ).status_code == 404
