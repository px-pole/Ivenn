# Tauri Update Signing Keys - Configuration Summary

## ✅ Successfully Generated

Tauri update signing keys have been generated and configured for auto-update functionality.

## Public Key (Already Installed)

The public key has been added to: `desktop/src-tauri/tauri.conf.json`

```
dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IEVFRDNEMTMxOUJDRTlGNEYKUldSUG44NmJNZEhUN29BdXd6U0ZOaE1YMVRJbzFycUNML3pERE5tZVp3M1hqRnM4RDNzdU0rL2QK
```

## Private Key (Store as GitHub Secret - NEVER in repo!)

⚠️ **CRITICAL SECURITY:** Keep the private key secret and NEVER commit it to git or store the password in any documentation.

The private key is currently stored at:
```
desktop/private-key.txt
```

### To add to GitHub Secrets (Correct Way):

1. Read the private key file content:
   ```bash
   cat desktop/private-key.txt
   ```

2. Go to: https://github.com/YOUR-ORG/inventory-vault/settings/secrets/actions

3. Create secret: `TAURI_SIGNING_PRIVATE_KEY`
   - Paste the private key file contents

4. Create secret: `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`
   - Paste the password (this should ONLY be stored in GitHub Secrets, not in git)

5. **Then delete the local `desktop/private-key.txt` file:**
   ```bash
   rm desktop/private-key.txt desktop/private-key.txt.pub
   ```

## Security Best Practices

✅ **DO:**
- Store private key in GitHub Secrets only
- Store password in GitHub Secrets only
- Use a strong, random password
- Keep GitHub account secure
- Rotate keys if compromised

❌ **DON'T:**
- Commit private key to git
- Document password in README/SIGNING_KEYS_CONFIG.md
- Share password with team members
- Use simple passwords like "password123"
- Leave private key files on your computer after adding to GitHub Secrets

## Next Steps

### 1. Prepare Repository

```bash
cd /home/karol/Documents/HIW-Vault/inventory-vault

# Update your GitHub repo URL in tauri.conf.json endpoints
# Change: "https://api.github.com/repos/your-org/inventory-vault/releases/latest"
# To your actual org/username
```

### 2. Add GitHub Secrets

Visit: https://github.com/YOUR-ORG/inventory-vault/settings/secrets/actions

Create two secrets (see steps above in "To add to GitHub Secrets")

### 3. Delete Local Key Files

After adding to GitHub Secrets:
```bash
rm desktop/private-key.txt desktop/private-key.txt.pub
```

### 4. Create First Release

```bash
git add desktop/src-tauri/tauri.conf.json SIGNING_KEYS_CONFIG.md
git commit -m "chore: configure auto-update signing keys"

git tag v0.1.0
git push origin main
git push origin v0.1.0
```

### 5. GitHub Actions Automatic Build

When you push the tag:
- Automatically detects version tag
- Builds installers for Windows, macOS, and Linux
- Signs them with your private key
- Creates GitHub release with installation instructions
- Attachs signed installers to release

### 6. Auto-Update Available to Users

When users run the installed app:
- App checks GitHub for newer version
- If available, downloads silently
- User notified at startup
- Update installed on next restart
- Signature verified automatically
- Update is installed automatically

## Files Generated

- `desktop/private-key.txt` - **Private key file (delete after adding to GitHub Secrets)**
- `desktop/private-key.txt.pub` - Public key (now in tauri.conf.json)

## Verification

To verify everything is configured:

```bash
# Build a test release
cd desktop
npm run tauri build --no-bundle

# Check that signed artifacts would be created
# (Actual signing only happens on release with GitHub Actions)
```

## Troubleshooting

**"Public key doesn't match"** during release:
- Regenerate keys with a new password
- Update both GitHub secrets with new values
- Update public key in `tauri.conf.json`
- Rebuild and redeploy

**Update not working:**
- Check `tauri.conf.json` version matches git tag
- Verify GitHub API endpoint is correct
- Ensure release is published (not draft)
- Check signing secrets are in GitHub secrets

**Need to rotate keys:**
```bash
cd desktop
# Generate new keys (you'll need a new password)
npx tauri signer generate -w ./private-key-new.txt --ci --force -p YOUR_NEW_SECURE_PASSWORD
# Then:
# 1. Update GitHub secrets with new key and password
# 2. Update public key in tauri.conf.json
# 3. Delete old private key files locally
# 4. Commit and release
```

## Additional Security

- Private key password should be strong and random (minimum 32 characters)
- Store password ONLY in GitHub Secrets, never in documentation or version control
- Rotate keys every 1-2 years or if compromised
- Keep GitHub account secure with 2FA enabled
- Review GitHub Actions logs for any signing errors
