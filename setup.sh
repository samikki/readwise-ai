#!/usr/bin/env bash
# Create the venv (if missing) and install/update all requirements.
# Run this once after cloning, and again whenever requirements.txt changes.

set -euo pipefail
cd "$(dirname "$0")"

VENV=venv

if [ ! -f "$VENV/bin/python" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
fi

echo "Installing requirements..."
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r requirements.txt

echo "Done. Run ./run_build.sh or ./run_sync.sh"
