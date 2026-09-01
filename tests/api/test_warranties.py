from datetime import date, timedelta

from tests.factories.model_factories import make_category, make_room, make_user


def _create_item(client, db_session, name="Fridge", user=None):
    user = user or make_user(db_session, email=f"{name.lower()}@example.com")
    room = make_room(db_session, name=f"{name}-room")
    category = make_category(db_session, name=f"{name}-category")
    response = client.post(
        "/items",
        json={"name": name, "room_id": str(room.id), "category_id": str(category.id), "user_id": str(user.id)},
    )
    return response.json()["id"]


def test_create_get_update_delete_warranty(client, db_session):
    item_id = _create_item(client, db_session)
    expires_on = (date.today() + timedelta(days=10)).isoformat()

    response = client.post(f"/items/{item_id}/warranty", json={"provider": "Acme", "expires_on": expires_on})
    assert response.status_code == 201

    response = client.get(f"/items/{item_id}/warranty")
    assert response.status_code == 200
    assert response.json()["provider"] == "Acme"

    response = client.patch(f"/items/{item_id}/warranty", json={"provider": "NewCo"})
    assert response.status_code == 200
    assert response.json()["provider"] == "NewCo"

    response = client.delete(f"/items/{item_id}/warranty")
    assert response.status_code == 204

    response = client.get(f"/items/{item_id}/warranty")
    assert response.status_code == 404


def test_create_duplicate_warranty_returns_409(client, db_session):
    item_id = _create_item(client, db_session)
    expires_on = date.today().isoformat()

    client.post(f"/items/{item_id}/warranty", json={"expires_on": expires_on})
    response = client.post(f"/items/{item_id}/warranty", json={"expires_on": expires_on})

    assert response.status_code == 409


def test_expiring_warranties_dashboard(client, db_session):
    soon_id = _create_item(client, db_session, name="Oven")
    client.post(
        f"/items/{soon_id}/warranty",
        json={"expires_on": (date.today() + timedelta(days=20)).isoformat()},
    )

    far_out_id = _create_item(client, db_session, name="Boiler")
    client.post(
        f"/items/{far_out_id}/warranty",
        json={"expires_on": (date.today() + timedelta(days=200)).isoformat()},
    )

    response = client.get("/warranties/expiring", params={"within": 30})
    assert response.status_code == 200
    body = response.json()
    assert [item["item_id"] for item in body] == [soon_id]
    assert body[0]["days_until_expiry"] == 20


def test_list_warranties_includes_expired_and_future_coverage(client, db_session):
    user = make_user(db_session)
    expired_id = _create_item(client, db_session, name="Expired Toaster", user=user)
    future_id = _create_item(client, db_session, name="Future Fridge", user=user)
    client.post(
        f"/items/{expired_id}/warranty",
        json={"provider": "OldCo", "expires_on": (date.today() - timedelta(days=5)).isoformat()},
    )
    client.post(
        f"/items/{future_id}/warranty",
        json={"provider": "NewCo", "expires_on": (date.today() + timedelta(days=200)).isoformat()},
    )

    response = client.get("/warranties")
    assert response.status_code == 200
    body = response.json()
    assert [warranty["item_id"] for warranty in body] == [expired_id, future_id]
    assert body[0]["days_until_expiry"] == -5
    assert body[1]["days_until_expiry"] == 200


def test_versioned_warranty_list_is_user_scoped(client, db_session):
    first_item_id = _create_item(client, db_session, name="Owned Fridge")
    second_item_id = _create_item(client, db_session, name="Other Fridge")
    client.post(
        f"/items/{first_item_id}/warranty",
        json={"expires_on": (date.today() + timedelta(days=10)).isoformat()},
    )
    client.post(
        f"/items/{second_item_id}/warranty",
        json={"expires_on": (date.today() + timedelta(days=20)).isoformat()},
    )

    response = client.get("/api/v1/warranties")
    assert response.status_code == 200
    assert [warranty["item_id"] for warranty in response.json()] == [first_item_id]
