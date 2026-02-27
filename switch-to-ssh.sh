#!/bin/bash
# Switch Git repository to SSH authentication

echo "🔄 Switching repository to SSH authentication..."

# Switch remote URL from HTTPS to SSH
git remote set-url origin git@github.com:zodraz/feedback-forge.git

echo "✅ Remote URL updated!"
echo ""
echo "Testing SSH connection..."

# Test SSH connection
ssh -T git@github.com 2>&1 | grep -q "successfully authenticated" && {
    echo "✅ SSH authentication successful!"
    echo ""
    echo "You can now push with:"
    echo "  git push -u origin main"
} || {
    echo "❌ SSH authentication failed."
    echo ""
    echo "Please add your SSH key to GitHub first:"
    echo "1. Go to: https://github.com/settings/keys"
    echo "2. Click 'New SSH key'"
    echo "3. Paste this key:"
    echo ""
    cat ~/.ssh/id_rsa.pub
    echo ""
    echo "Then run this script again."
}
