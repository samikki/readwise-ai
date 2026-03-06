#!/usr/bin/env python3
"""Generate an HTML summary from Readwise Reader and save it back to Readwise."""

import argparse
import logging
import sys
from datetime import datetime, timedelta

from readwise_ai.config import DEFAULT_DAYS, DEFAULT_MAX_ARTICLES, DEFAULT_SOURCE
from readwise_ai.readwise import fetch_documents, save_document
from readwise_ai.summariser import build_readwise_payload, filter_and_prioritise, generate_html_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate HTML summary from Readwise feed.")
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        choices=["new", "later", "shortlist", "archive", "feed"],
        help=f"Readwise Reader location to fetch from (default: {DEFAULT_SOURCE})",
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


def main() -> None:
    args = parse_args()

    updated_after = (datetime.now() - timedelta(days=args.days)).isoformat()
    raw_docs = fetch_documents(updated_after=updated_after, location=args.source)

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

    payload = build_readwise_payload(html, args.source)
    if not save_document(payload):
        sys.exit(1)


if __name__ == "__main__":
    main()
