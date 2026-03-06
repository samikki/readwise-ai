#!/usr/bin/env bash
# Create the venv (if missing) and install/update all requirements.
# Run this once after cloning, and again whenever requirements.txt changes.

set -euo pipefail
cd "$(dirname "$0")"

VENV=venv

if ! "$VENV/bin/python" --version &>/dev/null; then
    echo "Creating virtual environment..."
    python3 -m venv --clear "$VENV"
fi

echo "Installing requirements..."
"$VENV/bin/python" -m pip install -q --upgrade pip
"$VENV/bin/python" -m pip install -q -r requirements.txt

echo "Done. Run ./run_build.sh or ./run_sync.sh"
