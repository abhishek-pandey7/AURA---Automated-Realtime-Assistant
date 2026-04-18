#!/usr/bin/env bash
# AURA install script
# Run this once after cloning: bash install.sh

set -e

echo ""
echo "  ██████╗ ██╗   ██╗██████╗  █████╗ "
echo " ██╔══██╗██║   ██║██╔══██╗██╔══██╗"
echo " ███████║██║   ██║██████╔╝███████║"
echo " ██╔══██║██║   ██║██╔══██╗██╔══██║"
echo " ██║  ██║╚██████╔╝██║  ██║██║  ██║"
echo " ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝"
echo ""
echo "  Installing AURA..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
major=$(echo $python_version | cut -d. -f1)
minor=$(echo $python_version | cut -d. -f2)

if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 10 ]); then
    echo "  ✗ Python 3.10+ required. Found: $python_version"
    exit 1
fi
echo "  ✓ Python $python_version"

# Install package in editable mode
pip install -e . --quiet
echo "  ✓ AURA package installed"

# Install playwright browsers (optional — skip if it fails)
echo "  Installing Playwright browsers (for browser tools)..."
playwright install chromium 2>/dev/null && echo "  ✓ Playwright chromium installed" || echo "  ⚠ Playwright install skipped (browser tools won't work)"

# Set up .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✓ .env created from template"
    echo ""
    echo "  ⚠  ACTION REQUIRED:"
    echo "     Edit .env and fill in your InferX endpoint URL and API key."
    echo "     Then run: aura run"
else
    echo "  ✓ .env already exists"
fi

echo ""
echo "  ✓ Installation complete."
echo ""
echo "  Quick start:"
echo "    1. Edit .env with your InferX credentials"
echo "    2. Run: aura run"
echo ""
