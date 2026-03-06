#!/usr/bin/env python3
"""Generate a Frasier/Niles podcast script from Readwise Reader articles."""

import argparse
import logging
import sys
from datetime import datetime, timedelta

from readwise_ai.podcast import generate_podcast_script
from readwise_ai.readwise import fetch_documents
from readwise_ai.summariser import process_documents

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a podcast script from Readwise feed.")
    parser.add_argument(
        "--source",
        default="feed",
        choices=["new", "later", "shortlist", "archive", "feed"],
        help="Readwise Reader location to fetch from (default: feed)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="How many days back to fetch articles (default: 1)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap the number of articles fetched (useful for testing)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save the script to this file path instead of stdout",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    updated_after = (datetime.now() - timedelta(days=args.days)).isoformat()
    raw_docs = fetch_documents(updated_after=updated_after, location=args.source)

    if args.limit:
        raw_docs = raw_docs[: args.limit]

    if not raw_docs:
        logger.warning("No documents fetched — nothing to script.")
        sys.exit(0)

    sorted_tags = process_documents(raw_docs)

    if not sorted_tags:
        logger.warning("No tags to process after filtering.")
        sys.exit(0)

    script = generate_podcast_script(sorted_tags)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(script)
        logger.info("Saved script to %s", args.output)
    else:
        print(script)


if __name__ == "__main__":
    main()
