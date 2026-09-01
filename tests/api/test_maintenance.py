from app.core.config import settings
from app.services.backup import GeneratedFile


def test_versioned_backup_endpoint_returns_download_path(client, tmp_path, monkeypatch):
    artifact_path = tmp_path / "inventory-vault-backup.zip"
    artifact_path.write_bytes(b"backup")
    monkeypatch.setattr(
        "app.api.routes.maintenance.create_backup",
        lambda database_url, storage_dir: GeneratedFile(file_name=artifact_path.name, path=artifact_path),
    )

    response = client.post("/api/v1/maintenance/backup")

    assert response.status_code == 200
    assert response.json() == {
        "file_name": "inventory-vault-backup.zip",
        "download_path": "/maintenance/generated/inventory-vault-backup.zip",
    }


def test_versioned_export_can_be_downloaded(client, storage_dir):
    response = client.post("/api/v1/maintenance/export/csv")
    assert response.status_code == 200
    file_name = response.json()["file_name"]

    response = client.get(f"/api/v1/maintenance/generated/{file_name}")

    assert response.status_code == 200
    assert response.content.startswith(b"\xef\xbb\xbfRoom,Name")


def test_backup_is_disabled_for_authenticated_server_mode(client):
    original = settings.require_authentication
    settings.require_authentication = True
    try:
        response = client.post("/api/v1/maintenance/backup")
        assert response.status_code == 401
    finally:
        settings.require_authentication = original


def test_restore_status_is_consumed_after_read(client, storage_dir):
    status_path = storage_dir.parent / "restore-status.json"
    status_path.write_text('{"status":"success","message":"Restored","item_count":2,"attachment_count":1}')

    response = client.get("/api/v1/maintenance/restore-status")
    assert response.status_code == 200
    assert response.json()["item_count"] == 2
    assert client.get("/api/v1/maintenance/restore-status").json() is None
