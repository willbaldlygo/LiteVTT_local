#!/bin/bash
# LiteType — double-click launcher.
#
# First run: finds Python, creates a private virtual environment, installs
# LiteType from GitHub, and downloads a speech model.
# Every run after: just launches the menu-bar app.
#
# Non-technical users only need THIS file. Everything else is fetched and
# set up automatically.

APP_HOME="$HOME/.litetype"
VENV="$APP_HOME/venv"
PYTHON_MIN="3.11"
REPO="git+https://github.com/willbaldlygo/LiteVTT_local.git"
MODELS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/litetype/models"

echo "=========================================="
echo "                LiteType"
echo "=========================================="
echo ""

# --- 1. Find a Python 3.11+ interpreter ----------------------------------
find_python() {
    for cmd in python3.13 python3.12 python3.11 python3; do
        if command -v "$cmd" >/dev/null 2>&1; then
            ver=$("$cmd" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null) || continue
            # True when ver >= PYTHON_MIN
            if [ "$(printf '%s\n%s\n' "$PYTHON_MIN" "$ver" | sort -V | head -1)" = "$PYTHON_MIN" ]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON="$(find_python)"
if [ -z "$PYTHON" ]; then
    echo "❌ Python $PYTHON_MIN or newer is required, but none was found."
    echo ""
    echo "Opening the Python download page in your browser..."
    open "https://www.python.org/downloads/macos/"
    echo "Install Python, then double-click this file again."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

# --- 2. First-run setup ---------------------------------------------------
if [ ! -x "$VENV/bin/litetype" ]; then
    echo "📦 First-time setup — this can take a few minutes."
    echo ""

    if [ ! -d "$VENV" ]; then
        "$PYTHON" -m venv "$VENV" || {
            echo "❌ Failed to create the virtual environment."
            read -p "Press Enter to close..."
            exit 1
        }
    fi

    "$VENV/bin/pip" install --upgrade pip --quiet
    echo "📥 Installing LiteType..."
    if ! "$VENV/bin/pip" install "$REPO"; then
        echo "❌ Installation failed. Check your internet connection and try again."
        read -p "Press Enter to close..."
        exit 1
    fi
    echo "✅ LiteType installed."
    echo ""
fi

# --- 3. Ensure a speech model is present ---------------------------------
if ! ls "$MODELS_DIR"/*.bin >/dev/null 2>&1; then
    echo "🤖 No speech model found yet — let's download one."
    echo ""
    "$VENV/bin/litetype-download-models"
    echo ""
fi

# --- 4. Launch ------------------------------------------------------------
echo "🚀 Starting LiteType. Look for the 🎙️ icon in your menu bar."
echo "   Hold your hotkey (default Fn+Ctrl) to dictate."
echo ""
"$VENV/bin/litetype"

# Tidy up the Terminal window once the app exits.
osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1 || true
