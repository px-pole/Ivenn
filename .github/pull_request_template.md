## Summary

Describe the behavior changed and why.

## Validation

- [ ] `python -m pytest -q`
- [ ] `npm --prefix desktop run lint`
- [ ] `npm --prefix desktop run build`
- [ ] Native Tauri application opened successfully

## Platform coverage

- [ ] Windows
- [ ] Linux
- [ ] macOS
- [ ] Not platform-specific

For each platform tested, list the OS version, CPU architecture, package format, and any signing or runtime warnings. Untested platforms will be covered by CI, but call out platform-sensitive changes explicitly.

## Data and packaging

- [ ] Existing local SQLite data remains compatible
- [ ] The bundled backend starts and stops with Tauri
- [ ] No generated installers, databases, secrets, or build directories are committed
