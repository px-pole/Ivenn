def test_create_and_list_rooms(client):
    response = client.post("/rooms", json={"name": "Kitchen"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Kitchen"
    assert "id" in body

    response = client.get("/rooms")
    assert response.status_code == 200
    assert [room["name"] for room in response.json()] == ["Kitchen"]


def test_create_duplicate_room_returns_409(client):
    client.post("/rooms", json={"name": "Kitchen"})
    response = client.post("/rooms", json={"name": "Kitchen"})
    assert response.status_code == 409


def test_create_room_rejects_blank_name(client):
    response = client.post("/rooms", json={"name": ""})
    assert response.status_code == 422


def test_get_and_rename_room(client):
    room = client.post("/rooms", json={"name": "Spare Room"}).json()

    response = client.get(f"/rooms/{room['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Spare Room"

    response = client.patch(f"/rooms/{room['id']}", json={"name": "Office"})
    assert response.status_code == 200
    assert response.json()["name"] == "Office"


def test_rename_room_to_duplicate_returns_409(client):
    client.post("/rooms", json={"name": "Kitchen"})
    room = client.post("/rooms", json={"name": "Office"}).json()

    response = client.patch(f"/rooms/{room['id']}", json={"name": "Kitchen"})
    assert response.status_code == 409


def test_delete_empty_room(client):
    room = client.post("/rooms", json={"name": "Empty Room"}).json()

    response = client.delete(f"/rooms/{room['id']}")
    assert response.status_code == 204
    assert client.get(f"/rooms/{room['id']}").status_code == 404


def test_delete_room_with_items_returns_409(client, db_session):
    from tests.factories.model_factories import make_category, make_user

    room = client.post("/rooms", json={"name": "Kitchen"}).json()
    user = make_user(db_session)
    category = make_category(db_session)
    client.post(
        "/items",
        json={
            "name": "Kettle",
            "room_id": room["id"],
            "category_id": str(category.id),
            "user_id": str(user.id),
        },
    )

    response = client.delete(f"/rooms/{room['id']}")
    assert response.status_code == 409
    assert "contains 1 item" in response.json()["detail"]


def test_room_mutations_return_404_for_unknown_room(client):
    room_id = "00000000-0000-0000-0000-000000000000"

    assert client.get(f"/rooms/{room_id}").status_code == 404
    assert client.patch(f"/rooms/{room_id}", json={"name": "Office"}).status_code == 404
    assert client.delete(f"/rooms/{room_id}").status_code == 404
