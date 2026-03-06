#!/usr/bin/env bash
# Sync taste_profile.md from the Obsidian master file.
# Run this whenever you update your Obsidian taste profile.

set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f "venv/bin/python" ]; then
    echo "venv not found — run ./setup.sh first" >&2
    exit 1
fi

exec venv/bin/python sync_profile.py
