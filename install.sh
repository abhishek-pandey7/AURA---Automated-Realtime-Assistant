#!/usr/bin/env bash
# AURA install script — macOS / Linux
# Run once after cloning: bash install.sh

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

# ── Python version check ─────────────────────────────────────────────────────
python_cmd=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | awk '{print $2}')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            python_cmd="$cmd"
            break
        fi
    fi
done

if [ -z "$python_cmd" ]; then
    echo "  ✗ Python 3.10+ required. Please install it from https://python.org"
    exit 1
fi
echo "  ✓ Python $($python_cmd --version 2>&1 | awk '{print $2}')"

# ── macOS: install system audio libraries ────────────────────────────────────
if [[ "$OSTYPE" == "darwin"* ]]; then
    BREW=""
    for b in brew /opt/homebrew/bin/brew /usr/local/bin/brew; do
        if command -v "$b" &>/dev/null; then BREW="$b"; break; fi
    done

    if [ -z "$BREW" ]; then
        echo "  ⚠  Homebrew not found. Install it from https://brew.sh for voice support."
    else
        echo "  Installing macOS audio dependencies via Homebrew..."
        "$BREW" install portaudio flac --quiet 2>/dev/null && echo "  ✓ portaudio + flac installed" \
            || echo "  ⚠  brew install skipped (already installed or failed)"
    fi
fi

# ── Create virtual environment ────────────────────────────────────────────────
if [ ! -d ".venv" ]; then
    "$python_cmd" -m venv .venv
    echo "  ✓ Virtual environment created (.venv)"
else
    echo "  ✓ Virtual environment already exists"
fi

# Activate venv
source .venv/bin/activate

# ── Install Python dependencies ───────────────────────────────────────────────
pip install -e . --quiet
echo "  ✓ AURA package installed"

# ── macOS arm64: fix SpeechRecognition bundled flac binary ──────────────────
if [[ "$OSTYPE" == "darwin"* ]]; then
    ARCH=$(uname -m)
    SR_FLAC=".venv/lib/$(python3 -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')/site-packages/speech_recognition/flac-mac"
    BREW_FLAC=""
    for b in /opt/homebrew/bin/flac /usr/local/bin/flac; do
        if [ -f "$b" ]; then BREW_FLAC="$b"; break; fi
    done

    if [ -f "$SR_FLAC" ] && [ -n "$BREW_FLAC" ]; then
        BUNDLED_ARCH=$(file "$SR_FLAC" | grep -o 'x86_64\|arm64' || true)
        if [ "$BUNDLED_ARCH" = "x86_64" ] && [ "$ARCH" = "arm64" ]; then
            cp "$BREW_FLAC" "$SR_FLAC"
            echo "  ✓ Fixed SpeechRecognition flac binary (x86 → arm64)"
        fi
    fi
fi

# ── Playwright browsers ───────────────────────────────────────────────────────
echo "  Installing Playwright browsers (for browser tools)..."
playwright install chromium 2>/dev/null \
    && echo "  ✓ Playwright chromium installed" \
    || echo "  ⚠  Playwright install skipped (browser tools may not work)"

# ── .env setup ────────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✓ .env created from template"
    echo ""
    echo "  ⚠  ACTION REQUIRED:"
    echo "     Edit .env and fill in your API endpoint URL and key."
else
    echo "  ✓ .env already exists"
fi

echo ""
echo "  ✓ Installation complete."
echo ""
echo "  Quick start:"
echo "    source .venv/bin/activate"
echo "    aura run"
echo ""
