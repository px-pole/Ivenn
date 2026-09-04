# Changelog

## 0.1.21 - 2026-09-04

### Release

- Prepared the cross-platform Windows, Linux, and macOS release workflow.
- Targeted Node.js 24 in GitHub Actions.
- Included the Windows signing-step fix for empty certificate secrets.
- Published the current desktop, OCR, warranty, notification, export, and backup/restore work as the 0.1.21 release candidate.

## 0.1.2 - 2026-09-04

### Added

- Desktop item management with search, room/category/status filters, and item editing.
- Room and category management with safe in-use deletion guards.
- Attachment upload, download, deletion, and local receipt OCR suggestions.
- Warranty management and an in-app warranty expiry inbox.
- CSV, PDF, and complete SQLite-plus-attachments backup exports.
- Validated staged backup restore with checksum and SQLite integrity checks.
- Native Tauri builds for Windows, Linux, and macOS through platform CI.

### Changed

- Warranty reminders are now in-app only. No operating-system notifications or external notification service is used.
- Receipt PDF generation uses the cross-platform ReportLab renderer.
- Desktop data is stored in the operating system application-data directory.
