#!/usr/bin/env python3
"""Diagnostic: show exactly what gets fetched from each source and why."""

import json
from datetime import datetime, timedelta

from readwise_ai.readwise import fetch_documents

# Same window as the build script (1 day)
updated_after = (datetime.now() - timedelta(days=1)).isoformat()
print(f"Fetching articles updated after: {updated_after}\n")

for location in ("feed", "new"):
    docs = fetch_documents(updated_after=updated_after, location=location)
    print(f"{'='*60}")
    print(f"Location: {location!r}  —  {len(docs)} document(s) found")
    print(f"{'='*60}")
    for doc in docs:
        title = doc.get("title") or "(no title)"
        updated = doc.get("updated", "")[:19]
        saved_at = doc.get("saved_at", "")[:19]
        created_at = doc.get("created_at", "")[:19]
        summary = doc.get("summary") or ""
        has_summary = bool(summary.strip())
        tags_raw = doc.get("tags", {})
        tags = [v["name"] for v in tags_raw.values()] if isinstance(tags_raw, dict) else list(tags_raw)
        site = doc.get("site_name") or "(no site)"
        print(f"  title:      {title[:80]}")
        print(f"  site:       {site}")
        print(f"  updated:    {updated}")
        print(f"  saved_at:   {saved_at}")
        print(f"  created_at: {created_at}")
        print(f"  tags:       {tags}")
        print(f"  has_summary:{has_summary}  ({len(summary)} chars)")
        if has_summary:
            print(f"  summary:    {summary[:120]}...")
        print()
    print()
