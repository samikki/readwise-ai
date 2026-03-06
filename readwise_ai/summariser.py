import json
import logging
from datetime import datetime

from .config import DEFAULT_MAX_ARTICLES, IGNORE_TAGS, OPENAI_MODEL, PRIORITY_TAGS
from .openai_client import client

logger = logging.getLogger(__name__)


def _normalise_tags(raw_tags: dict | list) -> list[str]:
    if isinstance(raw_tags, dict):
        return [v["name"] for v in raw_tags.values()]
    return list(raw_tags)


def _priority_rank(doc: dict, priority_tags: list[str]) -> tuple[int, int]:
    """Sort key: (lowest priority tag index, unique-source flag inverted)."""
    tags = doc.get("tags", [])
    tag_rank = min(
        (priority_tags.index(t) for t in tags if t in priority_tags),
        default=len(priority_tags),
    )
    unique_source = 0 if doc.get("number_from_this_site", 1) == 1 else 1
    return (tag_rank, unique_source)


def filter_and_prioritise(
    raw_docs: list[dict],
    ignore_tags: list[str] = IGNORE_TAGS,
    priority_tags: list[str] = PRIORITY_TAGS,
    max_articles: int = DEFAULT_MAX_ARTICLES,
) -> list[dict]:
    """Filter unread docs, normalise tags, sort by priority, cap at max_articles.

    Returns a flat deduped list — one entry per article, no duplication across tags.
    """
    # Drop already-read items
    docs = [d for d in raw_docs if d.get("reading_progress", 0) < 2]

    # Count articles per site for the unique-source signal
    site_count: dict[str, int] = {}
    for doc in docs:
        site = doc.get("site_name") or ""
        site_count[site] = site_count.get(site, 0) + 1

    # Normalise tags and filter ignored
    processed: list[dict] = []
    for doc in docs:
        tags = _normalise_tags(doc.get("tags", {}))
        if any(t in ignore_tags for t in tags):
            continue
        doc_id = doc.get("id", "")
        processed.append(
            {
                "id": doc_id,
                "readwise_url": f"https://read.readwise.io/read/{doc_id}" if doc_id else None,
                "title": doc.get("title"),
                "author": doc.get("author"),
                "tags": tags,
                "summary": doc.get("summary"),
                "site_name": doc.get("site_name"),
                "source_url": doc.get("source_url"),
                "published_date": doc.get("published_date"),
                "number_from_this_site": site_count.get(doc.get("site_name") or "", 1),
            }
        )

    # Sort: priority tags first, unique sources first within ties
    processed.sort(key=lambda d: _priority_rank(d, priority_tags))

    # Cap and warn if truncated
    if len(processed) > max_articles:
        logger.warning(
            "Capping articles at %d (have %d). Increase --max-articles to include more.",
            max_articles,
            len(processed),
        )
        processed = processed[:max_articles]

    logger.info("%d articles selected for summary", len(processed))
    return processed


def generate_html_summary(docs: list[dict], model: str = OPENAI_MODEL) -> str:
    """Single OpenAI call → complete HTML document."""
    from .taste_profile import render_prompt  # imported here so missing-file errors surface at call time

    rendered = render_prompt(
        n_articles=len(docs),
        articles_json=json.dumps(docs, ensure_ascii=False, indent=2),
    )

    logger.info("Sending %d articles to %s", len(docs), model)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": rendered}],
    )

    body = response.choices[0].message.content
    return f"<html><body>{body}</body></html>"


def build_readwise_payload(html: str, source: str) -> dict:
    """Wrap generated HTML in the Readwise save API payload."""
    timestamp = datetime.now().isoformat()
    date_title = timestamp[:10].replace("-", ".")
    return {
        "url": f"https://example.com/summary{timestamp}",
        "title": f"Feed summary on {date_title} from {source}",
        "should_clean_html": False,
        "html": html,
        "tags": ["Summary"],
        "published_date": timestamp,
        "location": "new",
        "saved_using": "AI summarizer",
        "author": "AI",
        "category": "article",
    }
