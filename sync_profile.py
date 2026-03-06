#!/usr/bin/env python3
"""Sync taste_profile.md from the Obsidian master file.

Run this whenever you update your Obsidian taste profile:
    python sync_profile.py

Then review the diff, edit taste_profile.md if needed, and commit.
"""

import sys
from pathlib import Path

from readwise_ai.config import TASTE_PROFILE_SOURCE

src = Path(TASTE_PROFILE_SOURCE)
dst = Path("taste_profile.md")

if not src.exists():
    print(f"Source not found: {src}", file=sys.stderr)
    sys.exit(1)

import shutil

shutil.copy2(src, dst)
print(f"Synced: {src} → {dst}")
