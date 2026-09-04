# Auto-Update Mechanism

Ivenn uses Tauri's built-in updater to automatically check for and install new versions.

## How It Works

1. **Startup Check:** When the app starts, it checks GitHub releases for a newer version
2. **Background Download:** If available, the update is downloaded silently in the background
3. **User Notification:** User is notified of an available update
4. **Installation:** On next restart, the new version is installed and launched

## Configuration

### Setup Steps

1. **Generate signing keys** (required for secure updates):
   ```bash
   cd desktop
   npm run tauri -- signer generate -- -w YOUR_PASSWORD
   ```

   This outputs:
   - Private key (keep secret)
   - Public key (goes in config)

2. **Update `desktop/src-tauri/tauri.conf.json`:**
   ```json
   "updater": {
     "active": true,
     "dialog": true,
     "pubkey": "YOUR_PUBLIC_KEY_HERE",
     "endpoints": [
       "https://api.github.com/repos/YOUR_ORG/inventory-vault/releases/latest"
     ]
   }
   ```

3. **Store secrets in GitHub:**
   - `TAURI_SIGNING_PRIVATE_KEY` - The private key from step 1
   - `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` - Your password

4. **Version sync:** Keep `tauri.conf.json` version in sync with git tags:
   ```bash
   # Before release
   npm version patch  # Updates desktop/package.json and tauri.conf.json
   ```

## Release Workflow

The `.github/workflows/release.yml` handles:

1. **Detects version tags:** `git tag v0.2.0`
2. **Builds on all platforms** with signing
3. **Signs artifacts** using the private key
4. **Creates GitHub release** with `latest` tag
5. **Attaches installers** to release

Users' apps then discover the new version via the `endpoints` URL.

## GitHub API Rate Limiting

The updater checks GitHub releases, which has rate limits:
- Unauthenticated: 60 requests/hour per IP
- Authenticated: 5,000 requests/hour per user

For most users, 60/hour is sufficient. To increase limits:

1. Generate a GitHub Personal Access Token
2. Update the endpoint to include auth (not recommended for security)
3. Or use a custom update server (see below)

## Custom Update Server

Instead of GitHub releases, you can host updates on your own server:

1. **Create update metadata endpoint** that returns JSON:
   ```json
   {
     "version": "0.2.0",
     "notes": "Bug fixes and improvements",
     "pub_date": "2024-01-01T00:00:00Z",
     "platforms": {
       "windows-x86_64": {
         "signature": "...",
         "url": "https://myserver.com/releases/ivenn-0.2.0-x64.msi"
       },
       "darwin-aarch64": {
         "signature": "...",
         "url": "https://myserver.com/releases/ivenn-0.2.0-arm64.dmg"
       },
       "linux-x86_64": {
         "signature": "...",
         "url": "https://myserver.com/releases/ivenn-0.2.0-x64.AppImage"
       }
     }
   }
   ```

2. **Update endpoints in config:**
   ```json
   "updater": {
     "endpoints": [
       "https://myserver.com/updates/latest.json"
     ]
   }
   ```

3. **Sign artifacts** with your private key and include signature in metadata

## Manual Testing

Test updates without releasing to production:

1. **Build locally:**
   ```bash
   cd desktop
   npm run tauri build
   ```

2. **Manually create a release:**
   ```bash
   gh release create v0.1.5 ./dist/**/*
   ```

3. **Change version in tauri.conf.json to 0.1.4**

4. **Run the old version** and check for updates

## Disabling Auto-Updates

To temporarily disable (e.g., during testing):

```json
"updater": {
  "active": false
}
```

## Troubleshooting

**Updates not found:**
- Check version in tauri.conf.json matches git tag
- Verify GitHub API endpoint is accessible
- Check release is published (not draft)

**Signature verification failed:**
- Regenerate signing keys
- Ensure both private and public keys match
- Check `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` is correct

**Slow downloads:**
- GitHub API enforces rate limits
- Consider custom update server for high-volume apps
- Add retry logic in custom endpoints

## Security Notes

- Update signing uses cryptographic signatures to prevent tampering
- Only updates signed with your private key can be installed
- Always keep private key secure and never commit to git
- GitHub release assets are immutable (can't be modified after upload)
