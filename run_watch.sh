#!/usr/bin/env bash
# Generate and post a short watch summary to Readwise.
# Runs build.py --watch with any additional arguments forwarded.

set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f "venv/bin/python" ]; then
    echo "venv not found — run ./setup.sh first" >&2
    exit 1
fi

# Delete log files older than 14 days
find logs -type f -name "watch-*.log" -mtime +14 -delete 2>/dev/null || true

exec venv/bin/python build.py --watch "$@"
