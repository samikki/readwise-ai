#!/usr/bin/env bash
# Generate and post the daily HTML summary to Readwise.
# All arguments are forwarded to build.py, e.g.:
#   ./run_build.sh --dry-run --output test.html
#   ./run_build.sh --days 3 --max-articles 80

set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f "venv/bin/python" ]; then
    echo "venv not found — run ./setup.sh first" >&2
    exit 1
fi

# Delete log files older than 14 days
find logs -name "build-*.log" -mtime +14 -delete 2>/dev/null || true

exec venv/bin/python build.py "$@"
