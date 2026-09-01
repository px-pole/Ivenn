import hashlib
import json
import sqlite3
import zipfile
from contextlib import closing

from app.services.backup import apply_pending_restore, create_backup, get_generated_file, read_restore_status, write_export


def _create_restore_database(path, item_name):
    with closing(sqlite3.connect(path)) as database:
        with database:
            for table in ("users", "rooms", "categories", "attachments", "warranties"):
                database.execute(f"CREATE TABLE {table} (id TEXT PRIMARY KEY)")
            database.execute("CREATE TABLE household_items (id TEXT PRIMARY KEY, name TEXT)")
            database.execute("INSERT INTO household_items VALUES ('item-1', ?)", (item_name,))
            database.commit()


def test_create_backup_contains_consistent_database_manifest_and_uploads(tmp_path):
    database_path = tmp_path / "inventory.db"
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    attachment = uploads / "receipt.png"
    attachment.write_bytes(b"receipt-image")

    with closing(sqlite3.connect(database_path)) as database:
        with database:
            database.execute("CREATE TABLE household_items (id TEXT PRIMARY KEY)")
            database.execute("CREATE TABLE attachments (id TEXT PRIMARY KEY)")
            database.execute("INSERT INTO household_items VALUES ('item-1')")
            database.execute("INSERT INTO attachments VALUES ('attachment-1')")
            database.commit()

    artifact = create_backup(f"sqlite:///{database_path}", str(uploads))

    with zipfile.ZipFile(artifact.path) as archive:
        assert sorted(archive.namelist()) == ["inventory.db", "manifest.json", "uploads/receipt.png"]
        manifest = json.loads(archive.read("manifest.json"))
        restored_database = tmp_path / "restored.db"
        restored_database.write_bytes(archive.read("inventory.db"))

    assert manifest["format_version"] == 1
    assert manifest["item_count"] == 1
    assert manifest["attachment_count"] == 1
    assert manifest["uploads"] == [
        {"name": "receipt.png", "sha256": hashlib.sha256(b"receipt-image").hexdigest()}
    ]
    with sqlite3.connect(restored_database) as database:
        assert database.execute("SELECT count(*) FROM household_items").fetchone()[0] == 1


def test_generated_files_are_confined_to_export_directory(tmp_path):
    uploads = tmp_path / "uploads"
    artifact = write_export(b"report", str(uploads), "pdf")

    assert get_generated_file(str(uploads), artifact.file_name) == artifact.path
    assert get_generated_file(str(uploads), "../inventory.db") is None


def test_apply_pending_restore_replaces_database_and_uploads(tmp_path):
    source_dir = tmp_path / "source"
    source_uploads = source_dir / "uploads"
    source_uploads.mkdir(parents=True)
    source_database = source_dir / "inventory.db"
    _create_restore_database(source_database, "Backed up item")
    (source_uploads / "receipt.pdf").write_bytes(b"backed-up-file")
    backup = create_backup(f"sqlite:///{source_database}", str(source_uploads))

    target_dir = tmp_path / "target"
    target_uploads = target_dir / "uploads"
    target_uploads.mkdir(parents=True)
    target_database = target_dir / "inventory.db"
    _create_restore_database(target_database, "Current item")
    (target_uploads / "old.pdf").write_bytes(b"old-file")
    (target_dir / "pending-restore.zip").write_bytes(backup.path.read_bytes())

    status = apply_pending_restore(f"sqlite:///{target_database}", str(target_uploads))

    assert status and status["status"] == "success"
    with sqlite3.connect(target_database) as database:
        assert database.execute("SELECT name FROM household_items").fetchone()[0] == "Backed up item"
    assert sorted(path.name for path in target_uploads.iterdir()) == ["receipt.pdf"]
    assert read_restore_status(str(target_uploads)) == status


def test_invalid_pending_restore_preserves_current_data(tmp_path):
    target_uploads = tmp_path / "uploads"
    target_uploads.mkdir()
    target_database = tmp_path / "inventory.db"
    _create_restore_database(target_database, "Current item")
    (target_uploads / "current.pdf").write_bytes(b"current-file")
    with zipfile.ZipFile(tmp_path / "pending-restore.zip", "w") as archive:
        archive.writestr("manifest.json", '{"format_version": 1, "database_sha256": "wrong", "uploads": []}')
        archive.write(target_database, "inventory.db")

    status = apply_pending_restore(f"sqlite:///{target_database}", str(target_uploads))

    assert status and status["status"] == "error"
    with sqlite3.connect(target_database) as database:
        assert database.execute("SELECT name FROM household_items").fetchone()[0] == "Current item"
    assert (target_uploads / "current.pdf").read_bytes() == b"current-file"
