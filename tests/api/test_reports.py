from tests.factories.model_factories import make_category, make_room, make_user


def test_inventory_report_pdf_endpoint(client, db_session):
    user = make_user(db_session)
    room = make_room(db_session)
    category = make_category(db_session)
    client.post(
        "/items",
        json={"name": "Washer", "room_id": str(room.id), "category_id": str(category.id), "user_id": str(user.id)},
    )

    response = client.get("/reports/inventory.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def test_inventory_report_csv_endpoint(client, db_session):
    user = make_user(db_session)
    room = make_room(db_session, name="Garage")
    category = make_category(db_session)
    client.post(
        "/items",
        json={"name": "Drill", "room_id": str(room.id), "category_id": str(category.id), "user_id": str(user.id)},
    )

    response = client.get("/reports/inventory.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Garage" in response.text
    assert "Drill" in response.text


def test_inventory_summary_endpoint(client, db_session):
    user = make_user(db_session)
    kitchen = make_room(db_session, name="Kitchen")
    garage = make_room(db_session, name="Garage")
    appliances = make_category(db_session, name="Appliances")
    tools = make_category(db_session, name="Tools")

    client.post(
        "/items",
        json={"name": "Fridge", "room_id": str(kitchen.id), "category_id": str(appliances.id), "user_id": str(user.id)},
    )
    client.post(
        "/items",
        json={"name": "Drill", "room_id": str(garage.id), "category_id": str(tools.id), "user_id": str(user.id)},
    )

    response = client.get("/reports/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 2
    assert body["active_items"] == 2
    assert body["rooms_count"] == 2
    assert body["categories_count"] == 2
