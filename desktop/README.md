# Ivenn Desktop

Tauri 2 desktop client for Ivenn, built with React, TypeScript, and Vite.

## Development

Launch the native client from this directory:

```bash
npm install
npm run tauri dev
```

Tauri starts and stops the local FastAPI backend automatically. The repository root must contain the configured `.venv` until the backend is bundled for release builds.

Use `npm run build` for a frontend production build and `npm run lint` for static checks.

## Release

Build the standalone backend sidecar and the current platform's native package together:

```bash
npm run tauri build
```

The installed application contains its own Python runtime and does not require the source repository or `.venv`.

Build Windows packages on Windows, macOS packages on macOS, and Linux packages on Linux. The repository CI compiles the complete native application on all three operating systems for every pull request.
