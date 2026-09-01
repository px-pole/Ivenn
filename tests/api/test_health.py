def test_health_check_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_versioned_api_exposes_client_capabilities(client):
    response = client.get("/api/v1/capabilities")

    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v1"
    assert body["attachments"]["max_upload_size_bytes"] == 10 * 1024 * 1024
    assert "image/jpeg" in body["attachments"]["mime_types"]
    assert body["receipt_extraction"]["applies_automatically"] is False


def test_versioned_api_preserves_existing_health_contract(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
