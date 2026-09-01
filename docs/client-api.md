# Inventory Vault Client API

Inventory Vault exposes a versioned HTTP API at `/api/v1`. The desktop client uses this contract. Any future client should use the same versioned routes rather than the legacy unprefixed aliases.

## Discovery

`GET /api/v1/capabilities` reports:

- API version
- Maximum attachment size
- Accepted attachment MIME types
- Whether receipt extraction is available
- MIME types accepted by receipt extraction
- Whether suggestions are applied automatically

Clients should use this response to enable or disable scan controls. Inventory and manual attachment features remain available when receipt extraction is unavailable.

## Authentication

Local desktop mode runs with `REQUIRE_AUTHENTICATION=false` and uses one local user. A network-accessible deployment must set `REQUIRE_AUTHENTICATION=true` and use bearer tokens from the authentication endpoints.

Do not expose the desktop sidecar port to a network. It is intentionally bound to `127.0.0.1`.

## Attachments

Upload an attachment with multipart form data:

```http
POST /api/v1/items/{item_id}/attachments
Content-Type: multipart/form-data

attachment_type=receipt
file=<binary image or PDF>
```

Supported attachment types are:

- `item_photo`
- `receipt`
- `warranty_document`
- `other`

List, download, and delete routes are scoped through the parent item:

```text
GET    /api/v1/items/{item_id}/attachments
GET    /api/v1/items/{item_id}/attachments/{attachment_id}
DELETE /api/v1/items/{item_id}/attachments/{attachment_id}
```

The server generates storage names. Client filenames are display metadata only and must never be treated as filesystem paths.

## Receipt extraction

Request structured suggestions from an uploaded receipt image:

```text
POST /api/v1/items/{item_id}/attachments/{attachment_id}/extract
```

JPEG, PNG, and WebP are accepted for extraction. PDFs may be stored but are not scanned in the current version.

The response contains the raw OCR text and optional field suggestions for:

- Merchant
- Purchase date
- Estimated value
- Model
- Serial number

Each suggestion includes `value`, `confidence`, and the source `evidence` line. Extraction does not modify the item.

A client must show suggestions for review. After confirmation, apply selected values with:

```text
PATCH /api/v1/items/{item_id}
```

This review-before-write rule prevents uncertain OCR output from silently overwriting inventory data.

## Errors

Clients should handle these status codes:

- `404`: item, attachment, or stored file was not found
- `413`: upload exceeds the advertised maximum size
- `415`: unsupported attachment or extraction format
- `422`: invalid request data
- `503`: local OCR engine is unavailable

Error responses use FastAPI's standard `{ "detail": ... }` shape.

## Inventory organisation and lifecycle

Rooms and categories support list, create, retrieve, rename, and deletion through `/api/v1/rooms` and `/api/v1/categories`. Deleting a room or category that still contains items returns `409`; clients must move those items first.

Inventory items support lifecycle filtering and deletion:

```text
GET    /api/v1/items?room_id=&category_id=&status=&warranty_status=&search=
DELETE /api/v1/items/{item_id}
```

Filters combine with AND semantics. Warranty status accepts `active`, `expired`, or `none`. Item deletion also removes its warranty, attachment database records, and stored attachment files.

## Warranties

Warranty coverage is one-to-one with an inventory item:

```text
POST   /api/v1/items/{item_id}/warranty
GET    /api/v1/items/{item_id}/warranty
PATCH  /api/v1/items/{item_id}/warranty
DELETE /api/v1/items/{item_id}/warranty
```

`expires_on` is required when creating coverage. Provider, policy/reference number, and notes are optional.

The complete user-scoped warranty dashboard is available from:

```text
GET /api/v1/warranties
```

Each record includes item name/status and `days_until_expiry`; negative values indicate expired coverage. Upcoming reminder windows remain available from `/api/v1/warranties/expiring?within=30|60|90`.

## In-app notifications

Warranty reminders are stored and displayed only inside Inventory Vault. Reading the inbox synchronizes current 90, 60, and 30-day warranty thresholds and deduplicates each warranty/window combination.

```text
GET   /api/v1/notifications
PATCH /api/v1/notifications/{notification_id}
POST  /api/v1/notifications/mark-all-read
```

PATCH accepts `is_read` and `is_dismissed`. Notifications are user-scoped. Dismissed notices remain dismissed, and deleting the associated warranty removes its notice during the next inbox synchronization. No OS push or external notification service is used.

## Local exports and backup

Desktop local mode can generate files before presenting a native save dialog:

```text
POST /api/v1/maintenance/export/csv
POST /api/v1/maintenance/export/pdf
POST /api/v1/maintenance/backup
```

Each operation returns a generated filename and a temporary download path. Generated files can be retrieved from:

```text
GET /api/v1/maintenance/generated/{file_name}
```

Backups use ZIP format version 1 and contain:

- `inventory.db`, created with SQLite's online backup API
- `manifest.json`, including counts and SHA-256 checksums
- `uploads/`, containing all attachment files

Full-database backup endpoints are disabled when `REQUIRE_AUTHENTICATION=true`. Restore is intentionally not performed against a running database. The desktop app copies a selected ZIP to `pending-restore.zip`, relaunches, and applies it before importing FastAPI or opening SQLAlchemy.

Restore validation rejects unsafe paths, symbolic links, unexpected files, unsupported format versions, checksum mismatches, missing tables, and failed SQLite integrity checks. Current data remains in place when validation fails, and the result is available once after restart from:

```text
GET /api/v1/maintenance/restore-status
```
