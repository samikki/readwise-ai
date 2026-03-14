import json
import logging
from datetime import datetime

from pathlib import Path

from .config import DEFAULT_MAX_ARTICLES, IGNORE_TAGS, OPENAI_MODEL, OUTPUT_LANGUAGE, READER_NAME, SUMMARY_URL_PREFIX, WATCH_TAG, WATCH_URL_PREFIX
from .openai_client import client

logger = logging.getLogger(__name__)


def _normalise_tags(raw_tags: dict | list) -> list[str]:
    if isinstance(raw_tags, dict):
        return [v["name"] for v in raw_tags.values()]
    return list(raw_tags)


def filter_and_prioritise(
    raw_docs: list[dict],
    ignore_tags: list[str] = IGNORE_TAGS,
    max_articles: int = DEFAULT_MAX_ARTICLES,
) -> list[dict]:
    """Filter ignored tags and cap at max_articles.

    All articles from the timeframe are included regardless of read status.
    Ordering and priority is fully delegated to the AI model via the
    taste profile and local profile.
    """
    processed: list[dict] = []
    for doc in raw_docs:
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
            }
        )

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
        language=OUTPUT_LANGUAGE,
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
        "url": f"{SUMMARY_URL_PREFIX}{timestamp}",
        "title": f"{READER_NAME}'s briefing on {date_title} from {source}",
        "should_clean_html": False,
        "html": html,
        "tags": ["Summary"],
        "published_date": timestamp,
        "location": "new",
        "saved_using": "AI summarizer",
        "author": "AI",
        "category": "article",
    }


# --- Watch summary (short, glanceable) ---

_WATCH_TEMPLATE_PATH = Path(__file__).parent.parent / "watch_prompt_template.md"


def generate_watch_summary(docs: list[dict], model: str = OPENAI_MODEL) -> str:
    """Single OpenAI call → short plain-text watch briefing."""
    from .taste_profile import render_prompt

    rendered = render_prompt(
        n_articles=len(docs),
        articles_json=json.dumps(docs, ensure_ascii=False, indent=2),
        language=OUTPUT_LANGUAGE,
        template_path=_WATCH_TEMPLATE_PATH,
    )

    logger.info("Sending %d articles to %s for watch summary", len(docs), model)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": rendered}],
    )

    return response.choices[0].message.content


def build_watch_payload(text: str, source: str) -> dict:
    """Wrap plain-text watch summary in the Readwise save API payload."""
    timestamp = datetime.now().isoformat()
    date_title = timestamp[:10].replace("-", ".")
    # Wrap plain text in minimal HTML for Readwise (preserving line breaks)
    html_body = text.replace("\n", "<br>\n")
    return {
        "url": f"{WATCH_URL_PREFIX}{timestamp}",
        "title": f"{READER_NAME}'s watch briefing on {date_title}",
        "summary": text,  # Plain text in summary field — returned by list API
        "should_clean_html": False,
        "html": f"<html><body><p>{html_body}</p></body></html>",
        "tags": [WATCH_TAG],
        "published_date": timestamp,
        "location": "new",
        "saved_using": "AI summarizer",
        "author": "AI",
        "category": "article",
    }
