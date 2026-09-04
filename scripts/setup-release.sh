#!/usr/bin/env bash
# Quick setup script for Ivenn release configuration
# Run this once to set up auto-update signing

set -e

echo "🚀 Ivenn Release Setup"
echo "===================="
echo ""
echo "This script will help you set up Tauri auto-update signing."
echo "You'll need to:"
echo "  1. Generate signing keys"
echo "  2. Store them as GitHub secrets"
echo "  3. Update the configuration"
echo ""

# Check if we're in the right directory
if [ ! -f "desktop/src-tauri/tauri.conf.json" ]; then
    echo "❌ Error: Run this script from the repository root"
    exit 1
fi

echo "Step 1: Generate Tauri update signing keys"
echo "==========================================="
echo ""
echo "You'll be prompted to enter a password (store it securely!)"
echo ""

cd desktop

# Generate the keys
npm run tauri signer generate -- -w tauri.key

echo ""
echo "✅ Signing keys generated!"
echo ""
echo "Step 2: Save keys as GitHub secrets"
echo "===================================="
echo ""
echo "1. Go to: https://github.com/YOUR-ORG/inventory-vault/settings/secrets/actions"
echo ""
echo "2. Create two new secrets:"
echo ""
echo "   Secret 1: TAURI_SIGNING_PRIVATE_KEY"
echo "   Value: (contents of tauri.key file)"
echo ""
echo "   Secret 2: TAURI_SIGNING_PRIVATE_KEY_PASSWORD"
echo "   Value: (the password you just entered)"
echo ""
echo "3. Then delete the local tauri.key file:"
echo "   rm tauri.key"
echo ""

echo "Step 3: Update configuration"
echo "============================"
echo ""
echo "The public key is displayed above. Update it in:"
echo "  desktop/src-tauri/tauri.conf.json"
echo ""
echo "Find the updater.pubkey field and paste the public key there."
echo ""

echo "Step 4: Update repository URL"
echo "============================="
echo ""
echo "In desktop/src-tauri/tauri.conf.json, update:"
echo ""
echo '  "endpoints": ['
echo '    "https://api.github.com/repos/YOUR-ORG/inventory-vault/releases/latest"'
echo '  ]'
echo ""
echo "Replace YOUR-ORG with your GitHub organization/user name."
echo ""

echo "Step 5: Create first release"
echo "============================"
echo ""
echo "Now you're ready to create the first release:"
echo ""
echo "  git tag v0.1.0"
echo "  git push --tags"
echo ""
echo "The GitHub Actions workflow will automatically:"
echo "  1. Build installers for all platforms"
echo "  2. Sign them with your keys"
echo "  3. Create a GitHub release"
echo ""
echo "Users can then download and install, and their apps will"
echo "auto-update when you create new releases."
echo ""
echo "✅ Setup complete!"
