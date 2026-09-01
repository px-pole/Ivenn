from tests.factories.model_factories import make_category, make_room, make_user


def _create_item(client, db_session):
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
        },
    )
    return response.json()["id"]


def test_upload_attachment_returns_201(client, db_session, storage_dir):
    item_id = _create_item(client, db_session)

    response = client.post(
        f"/items/{item_id}/attachments",
        data={"attachment_type": "receipt"},
        files={"file": ("receipt.pdf", b"receipt-bytes", "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["attachment_type"] == "receipt"
    assert body["file_name"] == "receipt.pdf"
    assert "storage_key" not in body


def test_upload_attachment_rejects_unsupported_type(client, db_session, storage_dir):
    item_id = _create_item(client, db_session)

    response = client.post(
        f"/items/{item_id}/attachments",
        data={"attachment_type": "other"},
        files={"file": ("virus.exe", b"data", "application/x-msdownload")},
    )

    assert response.status_code == 415


def test_upload_attachment_for_unknown_item_returns_404(client, storage_dir):
    response = client.post(
        "/items/00000000-0000-0000-0000-000000000000/attachments",
        data={"attachment_type": "other"},
        files={"file": ("a.png", b"data", "image/png")},
    )

    assert response.status_code == 404


def test_list_and_delete_attachment(client, db_session, storage_dir):
    item_id = _create_item(client, db_session)
    upload_response = client.post(
        f"/items/{item_id}/attachments",
        data={"attachment_type": "item_photo"},
        files={"file": ("photo.jpg", b"photo-bytes", "image/jpeg")},
    )
    attachment_id = upload_response.json()["id"]

    response = client.get(f"/items/{item_id}/attachments")
    assert response.status_code == 200
    assert [a["id"] for a in response.json()] == [attachment_id]

    response = client.delete(f"/items/{item_id}/attachments/{attachment_id}")
    assert response.status_code == 204

    response = client.get(f"/items/{item_id}/attachments")
    assert response.json() == []


def test_download_attachment_returns_stored_file(client, db_session, storage_dir):
    item_id = _create_item(client, db_session)
    attachment = client.post(
        f"/items/{item_id}/attachments",
        data={"attachment_type": "receipt"},
        files={"file": ("receipt.png", b"image-bytes", "image/png")},
    ).json()

    response = client.get(f"/items/{item_id}/attachments/{attachment['id']}")
    assert response.status_code == 200
    assert response.content == b"image-bytes"
    assert response.headers["content-type"] == "image/png"


def test_extract_attachment_returns_structured_suggestions(client, db_session, storage_dir, monkeypatch):
    from app.schemas.attachment import ReceiptExtractionRead, ReceiptFieldSuggestion

    item_id = _create_item(client, db_session)
    attachment = client.post(
        f"/items/{item_id}/attachments",
        data={"attachment_type": "receipt"},
        files={"file": ("receipt.png", b"image-bytes", "image/png")},
    ).json()
    monkeypatch.setattr(
        "app.api.routes.attachments.extract_receipt",
        lambda path, mime_type: ReceiptExtractionRead(
            raw_text="Example Store\nTOTAL 49.99",
            merchant=ReceiptFieldSuggestion(value="Example Store", confidence=0.55, evidence="Example Store"),
            estimated_value=ReceiptFieldSuggestion(value="49.99", confidence=0.88, evidence="TOTAL 49.99"),
        ),
    )

    response = client.post(f"/items/{item_id}/attachments/{attachment['id']}/extract")
    assert response.status_code == 200
    assert response.json()["merchant"]["value"] == "Example Store"
    assert response.json()["estimated_value"]["value"] == "49.99"


def test_extract_pdf_returns_415(client, db_session, storage_dir):
    item_id = _create_item(client, db_session)
    attachment = client.post(
        f"/items/{item_id}/attachments",
        data={"attachment_type": "receipt"},
        files={"file": ("receipt.pdf", b"pdf-bytes", "application/pdf")},
    ).json()

    response = client.post(f"/items/{item_id}/attachments/{attachment['id']}/extract")
    assert response.status_code == 415


def test_versioned_attachment_upload_list_and_download(client, db_session, storage_dir):
    item_id = _create_item(client, db_session)
    response = client.post(
        f"/api/v1/items/{item_id}/attachments",
        data={"attachment_type": "receipt"},
        files={"file": ("receipt.png", b"versioned-image", "image/png")},
    )

    assert response.status_code == 201
    attachment_id = response.json()["id"]
    assert client.get(f"/api/v1/items/{item_id}/attachments").json()[0]["id"] == attachment_id
    assert client.get(f"/api/v1/items/{item_id}/attachments/{attachment_id}").content == b"versioned-image"
