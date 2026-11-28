#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# Friday CLI Installer
#
# Creates a global `friday` command at /usr/local/bin/friday that:
#   1. Activates the project's virtual environment automatically.
#   2. Passes through all CLI arguments.
#   3. Works from any directory.
#
# Usage:
#   chmod +x scripts/install.sh
#   ./scripts/install.sh
#
# To uninstall:
#   rm /usr/local/bin/friday
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

FRIDAY_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRIDAY_VENV="${FRIDAY_ROOT}/.venv"
INSTALL_PATH="/usr/local/bin/friday"

echo "Friday CLI Installer"
echo "===================="
echo ""
echo "  Project root : ${FRIDAY_ROOT}"
echo "  Virtual env  : ${FRIDAY_VENV}"
echo "  Install path : ${INSTALL_PATH}"
echo ""

# ── 1. Ensure virtual environment exists ─────────────────────────────────────
if [ ! -d "${FRIDAY_VENV}" ]; then
    echo "⚠  Virtual environment not found. Creating..."
    python3 -m venv "${FRIDAY_VENV}"
    echo "✓  Virtual environment created."
fi

# ── 2. Install project dependencies ─────────────────────────────────────────
echo "→  Installing dependencies..."
"${FRIDAY_VENV}/bin/pip" install --quiet -e "${FRIDAY_ROOT}"
echo "✓  Dependencies installed."

# ── 3. Write the global shim ─────────────────────────────────────────────────
SHIM_CONTENT="#!/bin/bash
# Friday CLI launcher — auto-activates the project virtual environment.
# Installed by scripts/install.sh — do not edit manually.

FRIDAY_ROOT=\"${FRIDAY_ROOT}\"
FRIDAY_VENV=\"\${FRIDAY_ROOT}/.venv/bin/python3\"

if [ ! -x \"\$FRIDAY_VENV\" ]; then
    echo \"Error: Friday virtual environment not found at \${FRIDAY_ROOT}/.venv\"
    echo \"Run:  cd \${FRIDAY_ROOT} && python3 -m venv .venv && .venv/bin/pip install -e .\"
    exit 1
fi

cd \"\$FRIDAY_ROOT\" || exit 1
exec \"\$FRIDAY_VENV\" main.py \"\$@\"
"

echo "→  Installing friday command to ${INSTALL_PATH}..."

if [ -w "$(dirname "${INSTALL_PATH}")" ]; then
    echo "${SHIM_CONTENT}" > "${INSTALL_PATH}"
    chmod +x "${INSTALL_PATH}"
else
    echo "   (requires sudo for /usr/local/bin)"
    echo "${SHIM_CONTENT}" | sudo tee "${INSTALL_PATH}" > /dev/null
    sudo chmod +x "${INSTALL_PATH}"
fi

echo "✓  friday command installed."
echo ""
echo "Done! You can now run 'friday' from any directory."
echo ""
echo "  friday --version    Show version"
echo "  friday --help       Show all available flags"
echo "  friday              Start interactive assistant"
