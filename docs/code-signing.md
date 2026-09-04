# Code Signing Setup Guide

This guide explains how to enable code signing for releases so users don't get security warnings when installing Ivenn.

## Why Code Signing?

- **Windows:** Prevents "Unknown Publisher" warnings
- **macOS:** Required for notarization and Gatekeeper acceptance
- **Linux:** Not required but can be done with GPG

## Windows Code Signing

### Prerequisites
- Authenticode certificate (from DigiCert, GlobalSign, etc.)
- NSIS (packaged by Tauri automatically)

### Setup

1. **Obtain a certificate:**
   - Purchase an Authenticode certificate from a trusted CA
   - Export as `.pfx` file with password

2. **Add secrets to GitHub:**
   ```
   WINDOWS_CERTIFICATE: (base64 encoded .pfx file)
   WINDOWS_CERTIFICATE_PWD: (certificate password)
   ```

3. **Update `desktop/src-tauri/tauri.conf.json`:**
   ```json
   "bundle": {
     "windows": [
       {
         "certificateThumbprint": "YOUR_THUMBPRINT",
         "signingIdentity": "your-company-name",
         "digestAlgorithm": "sha256",
         "timestampUrl": "http://timestamp.comodoca.com"
       }
     ]
   }
   ```

## macOS Code Signing & Notarization

### Prerequisites
- Apple Developer Account ($99/year)
- Mac hardware to build on (or Mac runner)

### Setup

1. **Generate signing certificate:**
   - Log in to [Apple Developer](https://developer.apple.com)
   - Create a "Developer ID Application" certificate
   - Export as `.p12` with password

2. **Add secrets to GitHub:**
   ```
   MACOS_CERTIFICATE: (base64 encoded .p12 file)
   MACOS_CERTIFICATE_PWD: (certificate password)
   MACOS_SIGNING_IDENTITY: (e.g., "Developer ID Application: Your Name (XXXXX)")
   APPLE_ID: (your Apple ID email)
   APPLE_PASSWORD: (app-specific password from appleid.apple.com)
   APPLE_TEAM_ID: (10-char team ID from developer.apple.com)
   ```

3. **Generate notarization credentials:**
   ```bash
   xcrun notarytool store-credentials "AC_PASSWORD" \
     --apple-id "$APPLE_ID" \
     --password "$APPLE_PASSWORD" \
     --team-id "$APPLE_TEAM_ID"
   ```

4. **Update `tauri.conf.json`:**
   ```json
   "bundle": {
     "macOS": [
       {
         "certificateThumbprint": "YOUR_THUMBPRINT",
         "signingIdentity": "YOUR_SIGNING_IDENTITY"
       }
     ]
   }
   ```

5. **Tauri will automatically notarize** during the build if credentials are configured.

## Update Signing (Tauri Updater)

The app uses Tauri's built-in updater for automatic updates. This requires signing:

1. **Generate signing keypair:**
   ```bash
   cd desktop
   npm run tauri -- signer generate -- -w SIGNING_PRIVATE_KEY_PASSWORD
   ```

2. **Save the keys:**
   - Private key → GitHub secret `TAURI_SIGNING_PRIVATE_KEY`
   - Public key → Update `tauri.conf.json` `updater.pubkey`
   - Password → GitHub secret `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`

3. **For the updater endpoint:**
   ```json
   "updater": {
     "endpoints": [
       "https://api.github.com/repos/YOUR_ORG/inventory-vault/releases/latest"
     ]
   }
   ```

## Linux GPG Signing (Optional)

1. **Create GPG key:**
   ```bash
   gpg --gen-key
   ```

2. **Export public key for distribution:**
   ```bash
   gpg --armor --export YOUR_KEY_ID > public-key.asc
   ```

3. **Sign releases in workflow:**
   ```bash
   gpg --armor --sign --detach-sig inventory-vault-*.AppImage
   ```

## GitHub Actions Configuration

All signing is configured in `.github/workflows/release.yml`:
- Secrets are passed via environment variables
- Platform-specific signing happens during `npm run tauri build`
- Signed artifacts are automatically uploaded to releases

## Local Development

For local development (not releases), you can skip signing:

```bash
cd desktop
npm run tauri dev
```

Building locally for testing also doesn't require signing:

```bash
npm run tauri build
```

Code signing only matters for official releases distributed to users.

## Testing

To verify signing works:

1. Push a tag: `git tag v0.2.0 && git push --tags`
2. Check the [Actions](https://github.com/your-org/inventory-vault/actions) tab
3. Review the draft release
4. Verify files are present and have signatures where enabled
5. Publish the release

## Troubleshooting

**"Certificate not found" on Windows:**
- Ensure .pfx file is base64 encoded correctly
- Verify certificate password is exact

**macOS notarization failed:**
- Check Apple ID is correct
- Ensure app-specific password is used (not main password)
- Verify team ID matches certificate

**Signature mismatch:**
- Regenerate signing keypair with `npm run tauri signer generate`
- Update both private key secret and public key in config

## Disabling Signing (for testing)

To temporarily disable signing, comment out signing configs in `tauri.conf.json` and remove secrets from GitHub Actions.
