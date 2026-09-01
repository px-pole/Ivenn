import uuid

from app.core.config import settings
from app.core.security import create_access_token
from tests.factories.model_factories import make_category, make_room, make_user


def test_create_item_returns_201(client, db_session):
    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)

    response = client.post(
        "/items",
        json={
            "name": "Washing Machine",
            "room_id": str(room.id),
            "category_id": str(category.id),
            "user_id": str(user.id),
            "serial_number": "SN-12345",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Washing Machine"
    assert body["status"] == "active"


def test_create_first_local_item_without_user_id(client, db_session):
    room = make_room(db_session)
    category = make_category(db_session)

    response = client.post(
        "/items",
        json={
            "name": "First local item",
            "room_id": str(room.id),
            "category_id": str(category.id),
        },
    )

    assert response.status_code == 201
    assert response.json()["user_id"]


def test_create_item_with_unknown_room_returns_422(client, db_session):
    user = make_user(db_session)
    category = make_category(db_session)

    response = client.post(
        "/items",
        json={
            "name": "Washing Machine",
            "room_id": str(user.id),
            "category_id": str(category.id),
            "user_id": str(user.id),
        },
    )

    assert response.status_code == 422


def test_get_item_not_found_returns_404(client):
    response = client.get("/items/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_items_search_and_filter(client, db_session):
    user = make_user(db_session)
    room = make_room(db_session, name="Kitchen")
    category = make_category(db_session, name="Appliances")

    create_response = client.post(
        "/items",
        json={
            "name": "Washing Machine",
            "room_id": str(room.id),
            "category_id": str(category.id),
            "user_id": str(user.id),
        },
    )
    item_id = create_response.json()["id"]

    response = client.get("/items", params={"search": "wash"})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [item_id]

    response = client.get("/items", params={"room_id": str(room.id)})
    assert [item["id"] for item in response.json()] == [item_id]

    response = client.get("/items", params={"search": "nonexistent"})
    assert response.json() == []


def test_list_items_filters_by_user_scope(client, db_session):
    alice = make_user(db_session, email="alice@example.com")
    bob = make_user(db_session, email="bob@example.com")
    kitchen = make_room(db_session, name="Kitchen")
    office = make_room(db_session, name="Office")
    appliances = make_category(db_session, name="Appliances")
    electronics = make_category(db_session, name="Electronics")

    alice_item = client.post(
        "/items",
        json={
            "name": "Washing Machine",
            "room_id": str(kitchen.id),
            "category_id": str(appliances.id),
            "user_id": str(alice.id),
        },
    ).json()["id"]
    client.post(
        "/items",
        json={
            "name": "Laptop",
            "room_id": str(office.id),
            "category_id": str(electronics.id),
            "user_id": str(bob.id),
        },
    )

    response = client.get("/items", params={"user_id": str(alice.id)})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [alice_item]

    response = client.get("/items", params={"user_id": str(bob.id)})
    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Laptop"]


def test_list_items_rejects_cross_user_scope_when_auth_is_required(client, db_session):
    original = settings.require_authentication
    settings.require_authentication = True
    try:
        alice = make_user(db_session, email="alice@example.com")
        bob = make_user(db_session, email="bob@example.com")
        kitchen = make_room(db_session, name="Kitchen")
        appliances = make_category(db_session, name="Appliances")

        client.post(
            "/items",
            json={
                "name": "Washing Machine",
                "room_id": str(kitchen.id),
                "category_id": str(appliances.id),
                "user_id": str(alice.id),
            },
        )
        client.post(
            "/items",
            json={
                "name": "Laptop",
                "room_id": str(kitchen.id),
                "category_id": str(appliances.id),
                "user_id": str(bob.id),
            },
        )

        alice_token = create_access_token(str(alice.id))
        response = client.get("/items", params={"user_id": str(bob.id)}, headers={"Authorization": f"Bearer {alice_token}"})
        assert response.status_code == 403
        assert response.json()["detail"] == "Forbidden"
    finally:
        settings.require_authentication = original


def test_update_item_status_endpoint(client, db_session):
    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)

    create_response = client.post(
        "/items",
        json={
            "name": "Laptop",
            "room_id": str(room.id),
            "category_id": str(category.id),
            "user_id": str(user.id),
        },
    )
    item_id = create_response.json()["id"]

    response = client.patch(f"/items/{item_id}/status", json={"status": "donated"})
    assert response.status_code == 200
    assert response.json()["status"] == "donated"


def test_update_item_fields(client, db_session):
    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)

    create_response = client.post(
        "/items",
        json={
            "name": "Laptop",
            "room_id": str(room.id),
            "category_id": str(category.id),
            "user_id": str(user.id),
        },
    )
    item_id = create_response.json()["id"]

    response = client.patch(f"/items/{item_id}", json={"brand": "Dell", "estimated_value": "899.99"})
    assert response.status_code == 200
    body = response.json()
    assert body["brand"] == "Dell"
    assert body["estimated_value"] == "899.99"


def test_delete_item_removes_warranty_attachment_record_and_file(client, db_session, storage_dir):
    from app.core.storage import resolve_path
    from app.db.models import Attachment, HouseholdItem, Warranty

    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)
    item = client.post(
        "/items",
        json={"name": "Laptop", "room_id": str(room.id), "category_id": str(category.id), "user_id": str(user.id)},
    ).json()
    client.post(f"/items/{item['id']}/warranty", json={"expires_on": "2030-01-01"})
    attachment = client.post(
        f"/items/{item['id']}/attachments",
        data={"attachment_type": "receipt"},
        files={"file": ("receipt.pdf", b"receipt", "application/pdf")},
    ).json()
    attachment_record = db_session.get(Attachment, uuid.UUID(attachment["id"]))
    stored_path = resolve_path(attachment_record.storage_key)

    response = client.delete(f"/items/{item['id']}")

    item_id = uuid.UUID(item["id"])
    assert response.status_code == 204
    assert db_session.get(HouseholdItem, item_id) is None
    assert db_session.query(Warranty).filter_by(item_id=item_id).count() == 0
    assert db_session.query(Attachment).filter_by(item_id=item_id).count() == 0
    assert not stored_path.exists()


def test_delete_item_returns_404_for_unknown_or_other_user(client, db_session):
    assert client.delete("/items/00000000-0000-0000-0000-000000000000").status_code == 404

    owner = make_user(db_session, email="delete-owner@example.com")
    other = make_user(db_session, email="delete-other@example.com")
    room = make_room(db_session)
    category = make_category(db_session)
    item_id = client.post(
        "/items",
        json={"name": "Private item", "room_id": str(room.id), "category_id": str(category.id), "user_id": str(owner.id)},
    ).json()["id"]

    original = settings.require_authentication
    settings.require_authentication = True
    try:
        token = create_access_token(str(other.id))
        response = client.delete(f"/items/{item_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 404
    finally:
        settings.require_authentication = original
