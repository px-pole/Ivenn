# Contributing to Ivenn

Thanks for contributing to Ivenn Inventory Vault. Contributions to the API, desktop client, translations, accessibility, documentation, tests, and native packaging are welcome. Native desktop packages must be built on the operating system they target, so platform-specific testing is particularly valuable.

## Development setup

Install these tools on every platform:

- Python 3.13 or newer
- Node.js 22 or newer
- Rust stable
- Git

Create the Python environment from the repository root:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Install the project and desktop dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
npm ci --prefix desktop
```

When running the API directly, create a local configuration file:

```bash
cp .env.example .env
```

Never commit `.env`, local databases, uploaded attachments, backups, or release artifacts.

### Platform prerequisites

Windows requires Microsoft C++ Build Tools and the WebView2 runtime. Current Windows 10 and Windows 11 installations normally include WebView2.

macOS requires Xcode Command Line Tools:

```bash
xcode-select --install
```

Ubuntu and Debian require Tauri's WebKit packages:

```bash
sudo apt-get update
sudo apt-get install -y libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf tesseract-ocr tesseract-ocr-eng
```

CachyOS and Arch Linux require:

```bash
sudo pacman -S webkit2gtk-4.1 tesseract tesseract-data-eng
```

## Run the desktop app

```bash
cd desktop
npm run tauri dev
```

This command builds the Python sidecar for the current platform, launches Tauri, creates the local SQLite database, and starts FastAPI automatically.

## Required checks

Run these before opening a pull request:

```bash
python -m pytest -q
npm --prefix desktop run lint
npm --prefix desktop run build
```

For user-facing desktop changes, check light and dark themes plus a narrow application window. Add or update the smallest relevant test for behavior changes.

Then verify the native application:

```bash
cd desktop
npm run tauri -- build --no-bundle
```

For packaging or release changes, also build the installer:

```bash
npm run tauri -- build
```

Artifacts are written under `desktop/src-tauri/target/release/bundle/`.

## Platform build report

Include this information in a platform-related pull request or issue:

- Operating system and version
- CPU architecture, such as x86_64 or arm64
- Python, Node.js, Rust, and Tauri versions
- Commands run and whether each completed successfully
- Package format tested
- Whether the app opened, created its database, and closed without leaving port 8765 in use
- Any signing, notarization, antivirus, or Gatekeeper messages

Do not commit generated binaries, installers, local databases, `.env` files, or build directories. Attach artifacts to the workflow run or release instead.

## Cross-platform expectations

- Use platform-neutral path APIs instead of hard-coded separators.
- Do not assume a Unix shell or `.venv/bin` layout.
- Keep user data in Tauri's operating-system application-data directory.
- Build PyInstaller sidecars natively for each target OS and architecture.
- Preserve keyboard access and layouts at the configured minimum window size.
- Keep the Windows, Linux, and macOS CI jobs green.

Unsigned local packages are suitable for testing. Public Windows and macOS releases will eventually require code-signing certificates; macOS distribution also requires notarization.

## Pull requests

Use the pull-request template. Include a concise behavior summary, commands run, and screenshots for visible UI changes. Keep unrelated refactors out of the pull request. Translation changes must include matching keys in every locale file, with English as the fallback.

## Reporting issues

For bugs, include the Ivenn version or commit, operating system, steps to reproduce, expected behavior, actual behavior, and relevant non-sensitive logs. Do not open a public issue for a security concern, data-loss risk, or exposure of household records; follow [SECURITY.md](SECURITY.md) instead.
