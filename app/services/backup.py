import hashlib
import json
import shutil
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.engine import make_url

BACKUP_FORMAT_VERSION = 1


class BackupUnsupportedError(Exception):
    """Raised when the active database cannot be backed up locally."""


class BackupValidationError(Exception):
    """Raised when a staged backup is unsafe or invalid."""


@dataclass(frozen=True)
class GeneratedFile:
    file_name: str
    path: Path


def _sqlite_path(database_url: str) -> Path:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database or url.database == ":memory:":
        raise BackupUnsupportedError("Local backup is available only for file-based SQLite databases")
    return Path(url.database).resolve()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_backup(database_url: str, storage_dir: str) -> GeneratedFile:
    database_path = _sqlite_path(database_url)
    app_data_dir = Path(storage_dir).resolve().parent
    export_dir = app_data_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    file_name = f"inventory-vault-backup-{timestamp}.zip"
    destination = export_dir / file_name

    if not database_path.is_file():
        raise BackupUnsupportedError("The local inventory database does not exist")

    with tempfile.TemporaryDirectory(dir=app_data_dir) as temporary_dir:
        snapshot_path = Path(temporary_dir) / "inventory.db"
        with sqlite3.connect(database_path) as source, sqlite3.connect(snapshot_path) as snapshot:
            source.backup(snapshot)

        with sqlite3.connect(snapshot_path) as snapshot:
            item_count = snapshot.execute("SELECT count(*) FROM household_items").fetchone()[0]
            attachment_count = snapshot.execute("SELECT count(*) FROM attachments").fetchone()[0]

        upload_dir = Path(storage_dir).resolve()
        upload_files = sorted(path for path in upload_dir.glob("*") if path.is_file()) if upload_dir.exists() else []
        manifest = {
            "format_version": BACKUP_FORMAT_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database_sha256": _sha256(snapshot_path),
            "item_count": item_count,
            "attachment_count": attachment_count,
            "uploads": [{"name": path.name, "sha256": _sha256(path)} for path in upload_files],
        }

        temporary_zip = destination.with_suffix(".tmp")
        with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(snapshot_path, "inventory.db")
            archive.writestr("manifest.json", json.dumps(manifest, indent=2))
            for path in upload_files:
                archive.write(path, f"uploads/{path.name}")
        temporary_zip.replace(destination)

    return GeneratedFile(file_name=file_name, path=destination)


def write_export(content: bytes, storage_dir: str, extension: str) -> GeneratedFile:
    if extension not in {"csv", "pdf"}:
        raise ValueError("Unsupported export format")
    export_dir = Path(storage_dir).resolve().parent / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    file_name = f"inventory-report-{timestamp}.{extension}"
    destination = export_dir / file_name
    destination.write_bytes(content)
    return GeneratedFile(file_name=file_name, path=destination)


def get_generated_file(storage_dir: str, file_name: str) -> Path | None:
    if Path(file_name).name != file_name:
        return None
    path = Path(storage_dir).resolve().parent / "exports" / file_name
    return path if path.is_file() else None


def _validate_member_names(archive: zipfile.ZipFile) -> None:
    total_size = 0
    for member in archive.infolist():
        path = Path(member.filename)
        if path.is_absolute() or ".." in path.parts:
            raise BackupValidationError("Backup contains an unsafe path")
        if (member.external_attr >> 16) & 0o170000 == 0o120000:
            raise BackupValidationError("Backup contains a symbolic link")
        if member.filename not in {"inventory.db", "manifest.json"} and not (
            len(path.parts) == 2 and path.parts[0] == "uploads"
        ):
            raise BackupValidationError("Backup contains an unexpected file")
        total_size += member.file_size
        if total_size > 4 * 1024 * 1024 * 1024:
            raise BackupValidationError("Backup is too large")


def _validate_snapshot(path: Path) -> None:
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
            if database.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise BackupValidationError("Backup database failed its integrity check")
            tables = {row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    except sqlite3.DatabaseError as exc:
        raise BackupValidationError("Backup database is not a valid SQLite file") from exc
    required_tables = {"users", "rooms", "categories", "household_items", "attachments", "warranties"}
    if not required_tables.issubset(tables):
        raise BackupValidationError("Backup database is missing required tables")


def apply_pending_restore(database_url: str, storage_dir: str) -> dict[str, object] | None:
    database_path = _sqlite_path(database_url)
    upload_dir = Path(storage_dir).resolve()
    app_data_dir = upload_dir.parent
    pending_path = app_data_dir / "pending-restore.zip"
    status_path = app_data_dir / "restore-status.json"
    if not pending_path.is_file():
        return None

    status: dict[str, object]
    try:
        with tempfile.TemporaryDirectory(dir=app_data_dir) as temporary_dir:
            temporary_path = Path(temporary_dir)
            snapshot_path = temporary_path / "inventory.db"
            restored_uploads = temporary_path / "uploads"
            restored_uploads.mkdir()

            with zipfile.ZipFile(pending_path) as archive:
                _validate_member_names(archive)
                try:
                    manifest = json.loads(archive.read("manifest.json"))
                    snapshot_path.write_bytes(archive.read("inventory.db"))
                except (KeyError, json.JSONDecodeError) as exc:
                    raise BackupValidationError("Backup is missing valid metadata or database content") from exc
                if manifest.get("format_version") != BACKUP_FORMAT_VERSION:
                    raise BackupValidationError("Backup format is not supported")
                if _sha256(snapshot_path) != manifest.get("database_sha256"):
                    raise BackupValidationError("Backup database checksum does not match")

                upload_manifest = manifest.get("uploads")
                if not isinstance(upload_manifest, list):
                    raise BackupValidationError("Backup upload metadata is invalid")
                expected_uploads: dict[str, str] = {}
                for entry in upload_manifest:
                    if not isinstance(entry, dict) or Path(str(entry.get("name", ""))).name != entry.get("name"):
                        raise BackupValidationError("Backup upload metadata is invalid")
                    expected_uploads[entry["name"]] = entry.get("sha256", "")
                archived_uploads = {
                    Path(name).name for name in archive.namelist() if len(Path(name).parts) == 2 and name.startswith("uploads/")
                }
                if archived_uploads != set(expected_uploads):
                    raise BackupValidationError("Backup upload files do not match the manifest")
                for name, checksum in expected_uploads.items():
                    restored_file = restored_uploads / name
                    restored_file.write_bytes(archive.read(f"uploads/{name}"))
                    if _sha256(restored_file) != checksum:
                        raise BackupValidationError(f"Backup checksum failed for upload '{name}'")

            _validate_snapshot(snapshot_path)
            previous_database = app_data_dir / "restore-previous.db"
            previous_uploads = app_data_dir / "restore-previous-uploads"
            previous_database.unlink(missing_ok=True)
            shutil.rmtree(previous_uploads, ignore_errors=True)
            database_moved = False
            uploads_moved = False
            try:
                if database_path.exists():
                    database_path.replace(previous_database)
                    database_moved = True
                if upload_dir.exists():
                    upload_dir.replace(previous_uploads)
                    uploads_moved = True
                snapshot_path.replace(database_path)
                restored_uploads.replace(upload_dir)
            except Exception:
                database_path.unlink(missing_ok=True)
                shutil.rmtree(upload_dir, ignore_errors=True)
                if database_moved:
                    previous_database.replace(database_path)
                if uploads_moved:
                    previous_uploads.replace(upload_dir)
                raise
            previous_database.unlink(missing_ok=True)
            shutil.rmtree(previous_uploads, ignore_errors=True)

        status = {
            "status": "success",
            "message": "Backup restored successfully",
            "item_count": manifest.get("item_count", 0),
            "attachment_count": manifest.get("attachment_count", 0),
        }
    except (BackupUnsupportedError, BackupValidationError, OSError, zipfile.BadZipFile) as exc:
        status = {"status": "error", "message": str(exc)}
    finally:
        pending_path.unlink(missing_ok=True)

    status_path.write_text(json.dumps(status), encoding="utf-8")
    return status


def read_restore_status(storage_dir: str, *, consume: bool = False) -> dict[str, object] | None:
    status_path = Path(storage_dir).resolve().parent / "restore-status.json"
    if not status_path.is_file():
        return None
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        status = {"status": "error", "message": "Restore status could not be read"}
    if consume:
        status_path.unlink(missing_ok=True)
    return status
