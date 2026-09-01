# Ivenn Inventory Vault

Ivenn is a private, desktop-first household inventory and warranty tracker for recording possessions, receipts, serial numbers, and replacement values. It helps households prepare insurance-ready exports and avoid missed warranty expirations.

## Features

- Inventory and room/category management
- Search and filtering by room, category, warranty state, and text
- Attachment uploads for receipts and item photos
- Warranty creation and upcoming-expiry tracking
- CSV and PDF inventory exports
- Persistent in-app warranty reminders

## Technology

| Area | Tools |
| --- | --- |
| Desktop client | Tauri 2, React, TypeScript, Vite |
| Local API | FastAPI, Pydantic, Uvicorn |
| Data | SQLite, SQLAlchemy, Alembic |
| Packaging | PyInstaller sidecar and Tauri native bundles |
| Receipt scanning | Tesseract OCR and Pillow |

## Local setup

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The app is available at `http://localhost:8001` by default. If port 8000 is already in use locally, the Docker setup will automatically use `APP_PORT` from `.env` or fall back to 8001.

## Database setup

```bash
alembic upgrade head
```

## Run tests

```bash
pytest -q
```

Before opening a pull request, also run:

```bash
npm --prefix desktop run lint
npm --prefix desktop run build
```

## Contributing

Contributions to the API, desktop client, translations, documentation, accessibility, tests, and native packaging are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for platform setup, required checks, and pull-request guidance. For security or data-loss reports, read [SECURITY.md](SECURITY.md).

## License

Ivenn Inventory Vault is available under the [MIT License](LICENSE).

## Docker setup

```bash
docker compose up --build
```

## Desktop app

The Tauri desktop client supports Windows, Linux, and macOS. Release packages must be built on their target operating system because PyInstaller and Tauri produce native binaries.

Platform prerequisites:

- **Windows:** Python 3.13+, Node.js 22+, Rust stable, and Microsoft C++ Build Tools with WebView2.
- **macOS:** Python 3.13+, Node.js 22+, Rust stable, and Xcode Command Line Tools. Distribution builds also require Apple code signing and notarization.
- **Linux:** Python 3.13+, Node.js 22+, Rust stable, WebKitGTK 4.1, and standard build tools.

On Arch Linux, install the native WebKit dependency once:

```bash
sudo pacman -S webkit2gtk-4.1 tesseract tesseract-data-eng
```

Tesseract and its English language data enable local receipt scanning. The inventory, attachments, and manual editing features continue to work when OCR is unavailable.

Warranty reminders appear only inside Inventory Vault. The app does not request operating-system notification permission or send reminder data to an external notification service.

Launch the desktop app with one command:

```bash
cd desktop
npm install
npm run tauri dev
```

Tauri starts FastAPI automatically on a private local port, applies database migrations, and stops the service when the desktop app closes. Desktop data is stored under the operating system's application-data directory; on Linux this defaults to `~/.local/share/com.inventoryvault.desktop/`.

The Data & Exports view saves CSV and PDF reports through a native system dialog. It also creates a complete ZIP backup containing a consistent SQLite snapshot, manifest checksums, and every uploaded attachment. Restore validates the backup, restarts the app, and replaces local data before the backend opens SQLite, avoiding file-lock problems on Windows.

The Python backend is bundled as a standalone sidecar, so running the compiled application does not require Python or the repository `.venv`. Building from source still uses `.venv` and requires the development dependencies:

```bash
pip install -e ".[dev]"
cd desktop
npm run tauri build
```

Build outputs use the native format for the current platform: Windows installers, macOS app/DMG bundles, and a Linux AppImage. Linux AppImages are written under `desktop/src-tauri/target/release/bundle/appimage/`.

The stable client-facing API is available under `/api/v1`. See [docs/client-api.md](docs/client-api.md) for attachment upload, receipt extraction, and confirmation behavior.

## Production notes

- Local development runs in a no-auth mode for convenience.
- Set `REQUIRE_AUTHENTICATION=true` when enabling a real user-bound deployment.
- The app runs migrations automatically through the Docker entrypoint before starting Uvicorn.

