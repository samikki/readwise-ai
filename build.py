#!/usr/bin/env python3
"""Generate an HTML summary from Readwise Reader and save it back to Readwise."""

import argparse
import logging
import sys
from datetime import datetime, timedelta

from readwise_ai.config import (
    DEFAULT_DAYS,
    DEFAULT_MAX_ARTICLES,
    DEFAULT_SOURCES,
    SUMMARY_RETENTION_DAYS,
)
from readwise_ai.readwise import delete_document, fetch_documents, save_document
from readwise_ai.summariser import build_readwise_payload, filter_and_prioritise, generate_html_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_VALID_SOURCES = ["new", "later", "shortlist", "archive", "feed"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate HTML summary from Readwise feed.")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=DEFAULT_SOURCES,
        choices=_VALID_SOURCES,
        metavar="SRC",
        help=f"Readwise Reader locations to fetch from (default: {' '.join(DEFAULT_SOURCES)}). "
             f"Choices: {', '.join(_VALID_SOURCES)}",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"How many days back to fetch articles (default: {DEFAULT_DAYS})",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=DEFAULT_MAX_ARTICLES,
        help=f"Maximum articles to pass to the model (default: {DEFAULT_MAX_ARTICLES})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate summary but do not post to Readwise",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Also save generated HTML to this file path",
    )
    return parser.parse_args()


def _fetch_all_sources(sources: list[str], updated_after: str) -> list[dict]:
    """Fetch documents from multiple Readwise locations, deduplicate by id."""
    all_docs: list[dict] = []
    seen_ids: set[str] = set()

    for source in sources:
        raw = fetch_documents(updated_after=updated_after, location=source)
        for doc in raw:
            doc_id = doc.get("id", "")
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                all_docs.append(doc)
            elif not doc_id:
                all_docs.append(doc)  # keep docs without id (shouldn't happen, but safe)

    logger.info(
        "Fetched %d unique documents from %s",
        len(all_docs),
        ", ".join(sources),
    )
    return all_docs


def _cleanup_old_summaries(retention_days: int) -> int:
    """Delete AI-generated summaries older than retention_days from Readwise.

    Identifies summaries by the 'Summary' tag (set by build_readwise_payload).
    Returns the number of documents deleted.
    """
    cutoff = datetime.now() - timedelta(days=retention_days)

    # Fetch documents from the last 60 days to find candidates — bounded search
    search_after = (datetime.now() - timedelta(days=60)).isoformat()
    docs = fetch_documents(updated_after=search_after)

    deleted = 0
    for doc in docs:
        # Identify summaries by tag
        raw_tags = doc.get("tags", {})
        if isinstance(raw_tags, dict):
            tag_names = [v["name"] for v in raw_tags.values()]
        else:
            tag_names = list(raw_tags)

        if "Summary" not in tag_names:
            continue

        # Check published date
        published = doc.get("published_date") or doc.get("created_at") or ""
        if not published:
            continue

        try:
            # Handle both timezone-aware and naive ISO timestamps
            pub_str = published.replace("Z", "+00:00")
            pub_dt = datetime.fromisoformat(pub_str).replace(tzinfo=None)
            if pub_dt < cutoff:
                doc_id = doc.get("id", "")
                title = doc.get("title", "(untitled)")
                if doc_id and delete_document(doc_id):
                    logger.info("Cleaned up old summary: %s (%s)", title, published[:10])
                    deleted += 1
        except (ValueError, KeyError):
            continue

    if deleted:
        logger.info("Deleted %d old summaries (retention: %d days)", deleted, retention_days)
    return deleted


def main() -> None:
    args = parse_args()

    # Clean up old summaries before generating a new one
    _cleanup_old_summaries(SUMMARY_RETENTION_DAYS)

    updated_after = (datetime.now() - timedelta(days=args.days)).isoformat()
    raw_docs = _fetch_all_sources(args.sources, updated_after)

    if not raw_docs:
        logger.warning("No documents fetched — nothing to summarise.")
        sys.exit(0)

    docs = filter_and_prioritise(raw_docs, max_articles=args.max_articles)

    if not docs:
        logger.warning("No articles remain after filtering.")
        sys.exit(0)

    html = generate_html_summary(docs)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Saved HTML to %s", args.output)

    if args.dry_run:
        logger.info("Dry run — skipping Readwise upload.")
        print(html)
        return

    source_label = "+".join(args.sources)
    payload = build_readwise_payload(html, source_label)
    if not save_document(payload):
        sys.exit(1)


if __name__ == "__main__":
    main()
