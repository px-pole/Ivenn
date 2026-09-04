# Release Process

This document outlines how to create and publish a new release of Ivenn.

## Pre-Release Checklist

- [ ] All changes merged to `main`
- [ ] All tests passing: `pytest -q && npm --prefix desktop run lint && npm --prefix desktop run build`
- [ ] Version bumped in all three application manifests (see below)
- [ ] `CHANGELOG.md` updated
- [ ] Code signing configured (see [docs/code-signing.md](code-signing.md))
- [ ] Auto-update signing keys generated (see [docs/auto-update.md](docs/auto-update.md))

## Bumping Version

Version is defined in two places:

1. **Python backend** - `pyproject.toml`:
   ```toml
   version = "0.1.21"
   ```

2. **Desktop app** - `desktop/src-tauri/tauri.conf.json`:
   ```json
   "version": "0.1.21"
   ```

3. **Node package** - `desktop/package.json`:
   ```json
   "version": "0.1.21"
   ```

All three must match the git tag exactly.

### Semi-Automatic Version Bump

From the desktop folder, use npm to bump version (updates package.json and tauri.conf.json):

```bash
npm version patch      # 0.1.5 → 0.1.6
npm version minor      # 0.1.5 → 0.2.0
npm version major      # 0.1.5 → 1.0.0
```

Then manually update `pyproject.toml` to match.

## Creating a Release

### Method 1: Git Tag (Recommended)

Tag triggers the release workflow automatically:

```bash
# Update versions first
npm version patch
# Update pyproject.toml version to match

# Commit version bump
git add pyproject.toml desktop/package.json desktop/src-tauri/tauri.conf.json
git commit -m "chore: bump version to 0.1.21"

# Create tag
git tag -a v0.1.21 -m "Release v0.1.21"

# Push commits and tag
git push origin main
git push origin v0.1.21
```

### Method 2: GitHub Release UI

1. Go to [Releases](https://github.com/your-org/inventory-vault/releases)
2. Click "Draft a new release"
3. Tag: `v0.1.21` (must match versions in config)
4. Title: "Ivenn v0.1.21"
5. Click "Auto-generate release notes"
6. Save as draft first

The workflow accepts an existing tag when run manually. For `0.1.2`, select or enter `v0.1.2` as the workflow tag input.

## Build Process

When a version tag is pushed or workflow is manually triggered:

1. **Release job creates:** GitHub release with platform-specific installation instructions
2. **Package jobs build on:** Windows, macOS, and Linux runners
3. **Each platform produces:**
   - Windows: `.exe` MSI installer
   - macOS: `.dmg` app bundle
   - Linux: `.AppImage`
4. **Artifacts signed** with private keys from secrets
5. **Artifacts uploaded** to the release as draft

## Publishing Release

When all Windows, Linux, and macOS package jobs succeed, the workflow publishes the release automatically. If any platform fails, the release remains a draft for investigation.

Before publishing a production release, verify the three uploaded platform artifacts and installation instructions in the draft release.

Users will be notified via:
- GitHub "Watch" notifications
- In-app update notification on startup

## Rollback

If a release has critical issues:

1. Delete the release and tag
2. Fix the issue
3. Create a new release with patch version bump

Old versions remain available in release history.

## Signing Configuration

Before first release, configure code signing per platform:

See [docs/code-signing.md](code-signing.md) for:
- Obtaining certificates
- Adding GitHub secrets
- Platform-specific setup

Without signing configured:
- Windows: Will show "Unknown Publisher" warning
- macOS: Will show Gatekeeper warning
- Linux: No restrictions (UNIX tradition)

Apps still function normally, but users must confirm installation.

## Update Mechanism

After first release:

1. **Subsequent releases** automatically detected by running apps
2. **Users notified** at startup if update available
3. **Updated** downloaded in background
4. **Installed** on next app restart

Update signing keys:
- Generated with: `npm run tauri signer generate`
- Store in GitHub secrets
- Update public key in `tauri.conf.json`

See [docs/auto-update.md](docs/auto-update.md) for details.

## Continuous Delivery

Alternative: Auto-publish releases from `main` or `release/*` branches.

To implement:

1. Update `.github/workflows/release.yml`:
   ```yaml
   on:
     workflow_dispatch:  # Manual trigger
     push:
       branches:
         - main
       tags:
         - 'v*'
   ```

2. Change release creation from `draft: true` to `draft: false`

3. Consider using conventional commits for automatic versioning

## Tips

- **Test locally first:** `npm run tauri dev` and `npm run tauri build`
- **Watch the Actions tab** for build progress and logs
- **Keep git history clean** (squash/rebase before tagging)
- **Test release in VM** before major announcements
- **Document breaking changes** in release notes
- **Tag only releases** - don't tag experimental builds

## Maintenance Releases

For maintenance on older versions:

1. Create branch from tag: `git checkout -b release/0.1.x v0.1.5`
2. Cherry-pick fixes: `git cherry-pick COMMIT_HASH`
3. Bump patch version: `v0.1.6`
4. Push and tag normally
5. If still supported, create release as usual

## Distribution Channels

After release, update:

- [ ] GitHub release page with checksums
- [ ] Download mirrors (if using CDN)
- [ ] Package managers (apt, homebrew, etc.) - optional
- [ ] Website documentation
- [ ] Changelog/blog if maintained
