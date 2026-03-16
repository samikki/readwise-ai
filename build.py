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
    SUMMARY_URL_PREFIX,
    WATCH_HOURS,
    WATCH_KEEP,
    WATCH_URL_PREFIX,
)
from readwise_ai.readwise import delete_document, fetch_documents, fetch_highlighted_urls, save_document
from readwise_ai.summariser import (
    build_readwise_payload,
    build_watch_payload,
    filter_and_prioritise,
    generate_html_summary,
    generate_watch_summary,
)

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
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Generate a short watch summary instead of the full briefing",
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


def _cleanup_old_summaries(retention_days: int, url_prefix: str = SUMMARY_URL_PREFIX) -> int:
    """Delete AI-generated summaries older than retention_days from Readwise.

    Identifies summaries by the given url_prefix (defaults to summary_url_prefix
    from config.toml), which is unique to this script and cannot collide with
    user content. Summaries with highlights are never deleted.
    Returns the number of documents deleted.
    """
    cutoff = datetime.now() - timedelta(days=retention_days)

    # Fetch highlight counts once up front (v2 API) to protect highlighted summaries
    highlighted = fetch_highlighted_urls(url_prefix)

    # Fetch documents from the last 60 days to find candidates — bounded search
    search_after = (datetime.now() - timedelta(days=60)).isoformat()
    docs = fetch_documents(updated_after=search_after)

    deleted = 0
    preserved = 0
    for doc in docs:
        # Only touch documents created by this script (identified by URL prefix)
        source_url = doc.get("source_url") or doc.get("url") or ""
        if not source_url.startswith(url_prefix):
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
                title = doc.get("title", "(untitled)")

                # Never delete summaries the user has highlighted
                if source_url in highlighted:
                    logger.info("Preserving highlighted summary: %s (%s)", title, published[:10])
                    preserved += 1
                    continue

                doc_id = doc.get("id", "")
                if doc_id and delete_document(doc_id):
                    logger.info("Cleaned up old summary: %s (%s)", title, published[:10])
                    deleted += 1
        except (ValueError, KeyError):
            continue

    if preserved:
        logger.info("Preserved %d highlighted summaries from deletion", preserved)
    if deleted:
        logger.info("Deleted %d old summaries (retention: %d days)", deleted, retention_days)
    return deleted


def _cleanup_keep_latest(url_prefix: str, keep: int = 3) -> int:
    """Delete all but the N most recent documents matching url_prefix.

    Identifies documents by URL prefix, sorts by published/created date,
    keeps the newest `keep` and deletes the rest. Summaries with highlights
    are never deleted. Returns count deleted.
    """
    # Fetch highlight counts once up front (v2 API)
    highlighted = fetch_highlighted_urls(url_prefix)

    search_after = (datetime.now() - timedelta(days=60)).isoformat()
    docs = fetch_documents(updated_after=search_after)

    # Find matching documents with their dates
    candidates: list[tuple[str, str, str, str]] = []  # (date_str, doc_id, title, source_url)
    for doc in docs:
        source_url = doc.get("source_url") or doc.get("url") or ""
        if not source_url.startswith(url_prefix):
            continue
        doc_id = doc.get("id", "")
        if not doc_id:
            continue
        date_str = doc.get("created_at") or doc.get("published_date") or ""
        title = doc.get("title", "(untitled)")
        candidates.append((date_str, doc_id, title, source_url))

    if len(candidates) <= keep:
        return 0

    # Sort by date descending (newest first), delete the rest
    candidates.sort(key=lambda x: x[0], reverse=True)
    to_delete = candidates[keep:]

    deleted = 0
    preserved = 0
    for date_str, doc_id, title, source_url in to_delete:
        if source_url in highlighted:
            logger.info("Preserving highlighted watch summary: %s", title)
            preserved += 1
            continue
        if delete_document(doc_id):
            logger.info("Cleaned up old watch summary: %s", title)
            deleted += 1

    if preserved:
        logger.info("Preserved %d highlighted watch summaries from deletion", preserved)
    if deleted:
        logger.info("Deleted %d old watch summaries (keeping %d latest)", deleted, keep)
    return deleted


def main() -> None:
    args = parse_args()

    if args.watch:
        _run_watch(args)
    else:
        _run_summary(args)


def _run_summary(args: argparse.Namespace) -> None:
    """Generate the full HTML briefing (existing behaviour)."""
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


def _run_watch(args: argparse.Namespace) -> None:
    """Generate a short watch summary."""
    updated_after = (datetime.now() - timedelta(hours=WATCH_HOURS)).isoformat()
    raw_docs = _fetch_all_sources(args.sources, updated_after)

    if not raw_docs:
        logger.info("No documents fetched for the watch window — skipping summary and upload.")
        sys.exit(0)

    docs = filter_and_prioritise(raw_docs, max_articles=args.max_articles)

    if not docs:
        logger.info("No articles remain after filtering — skipping summary and upload.")
        sys.exit(0)

    text = generate_watch_summary(docs)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info("Saved watch summary to %s", args.output)

    if args.dry_run:
        logger.info("Dry run — skipping Readwise upload.")
        print(text)
        return

    # Clean up old summaries only once we have a new one ready to replace them
    _cleanup_keep_latest(url_prefix=WATCH_URL_PREFIX, keep=WATCH_KEEP)

    source_label = "+".join(args.sources)
    payload = build_watch_payload(text, source_label)
    if not save_document(payload):
        sys.exit(1)


if __name__ == "__main__":
    main()
