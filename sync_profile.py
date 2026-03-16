#!/usr/bin/env python3
"""Sync taste_profile.md from an external source.

Copies the file specified by [profile] source in config.toml to taste_profile.md.
Useful when you maintain your taste profile in another tool (e.g. Obsidian)
and want to keep the local copy up to date.

    python sync_profile.py
"""

import shutil
import sys
from pathlib import Path

from readwise_ai.config import TASTE_PROFILE_SOURCE

src = Path(TASTE_PROFILE_SOURCE)
dst = Path("taste_profile.md")

if not src.exists():
    print(f"Source not found: {src}", file=sys.stderr)
    sys.exit(1)

shutil.copy2(src, dst)
print(f"Synced: {src} → {dst}")
