def test_create_and_list_categories(client):
    response = client.post("/categories", json={"name": "Electronics"})
    assert response.status_code == 201
    assert response.json()["name"] == "Electronics"

    response = client.get("/categories")
    assert response.status_code == 200
    assert [category["name"] for category in response.json()] == ["Electronics"]


def test_create_duplicate_category_returns_409(client):
    client.post("/categories", json={"name": "Electronics"})
    response = client.post("/categories", json={"name": "Electronics"})
    assert response.status_code == 409


def test_get_and_rename_category(client):
    category = client.post("/categories", json={"name": "Miscellaneous"}).json()

    assert client.get(f"/categories/{category['id']}").json()["name"] == "Miscellaneous"
    response = client.patch(f"/categories/{category['id']}", json={"name": "Appliances"})

    assert response.status_code == 200
    assert response.json()["name"] == "Appliances"


def test_rename_category_to_duplicate_returns_409(client):
    client.post("/categories", json={"name": "Electronics"})
    category = client.post("/categories", json={"name": "Appliances"}).json()

    assert client.patch(f"/categories/{category['id']}", json={"name": "Electronics"}).status_code == 409


def test_delete_empty_category(client):
    category = client.post("/categories", json={"name": "Empty"}).json()

    assert client.delete(f"/categories/{category['id']}").status_code == 204
    assert client.get(f"/categories/{category['id']}").status_code == 404


def test_delete_category_with_items_returns_409(client, db_session):
    from tests.factories.model_factories import make_room, make_user

    category = client.post("/categories", json={"name": "Electronics"}).json()
    room = make_room(db_session)
    user = make_user(db_session)
    client.post(
        "/items",
        json={"name": "Laptop", "room_id": str(room.id), "category_id": category["id"], "user_id": str(user.id)},
    )

    response = client.delete(f"/categories/{category['id']}")
    assert response.status_code == 409
    assert "contains 1 item" in response.json()["detail"]


def test_category_mutations_return_404_for_unknown_category(client):
    category_id = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/categories/{category_id}").status_code == 404
    assert client.patch(f"/categories/{category_id}", json={"name": "Unknown"}).status_code == 404
    assert client.delete(f"/categories/{category_id}").status_code == 404
