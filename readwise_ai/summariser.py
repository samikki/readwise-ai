import logging
from datetime import datetime

from .config import IGNORE_TAGS, OPENAI_MODEL, PRIORITY_TAGS
from .openai_client import client
from .prompts import html_segment_prompt

logger = logging.getLogger(__name__)


def _normalise_tags(raw_tags: dict | list) -> list[str]:
    if isinstance(raw_tags, dict):
        return [v["name"] for v in raw_tags.values()]
    return list(raw_tags)


def process_documents(
    raw_docs: list[dict],
    ignore_tags: list[str] = IGNORE_TAGS,
    priority_tags: list[str] = PRIORITY_TAGS,
) -> dict[str, list[dict]]:
    """Filter, normalise, and group documents by tag, sorted by priority."""
    # Drop already-read items
    docs = [d for d in raw_docs if d.get("reading_progress", 0) < 2]

    # Count articles per site
    site_count: dict[str, int] = {}
    for doc in docs:
        site = doc.get("site_name") or ""
        site_count[site] = site_count.get(site, 0) + 1

    # Normalise and filter
    processed: list[dict] = []
    for doc in docs:
        tags = _normalise_tags(doc.get("tags", {}))
        if any(t in ignore_tags for t in tags):
            continue
        processed.append(
            {
                "title": doc.get("title"),
                "author": doc.get("author"),
                "tags": tags,
                "summary": doc.get("summary"),
                "site_name": doc.get("site_name"),
                "source_url": doc.get("source_url"),
                "image_url": doc.get("image_url"),
                "published_date": doc.get("published_date"),
                "number_from_this_site": site_count.get(doc.get("site_name") or "", 1),
            }
        )

    logger.info("%d articles after filtering", len(processed))

    # Group by tag
    by_tag: dict[str, list[dict]] = {}
    for doc in processed:
        for tag in doc["tags"]:
            by_tag.setdefault(tag, []).append(doc)

    # Remove ignored tags and sort by priority
    by_tag = {t: v for t, v in by_tag.items() if t not in ignore_tags}
    sorted_tags = {
        k: v
        for k, v in sorted(
            by_tag.items(),
            key=lambda item: (
                priority_tags.index(item[0]) if item[0] in priority_tags else len(priority_tags),
                item[0],
            ),
        )
    }

    return sorted_tags


def generate_html_summary(
    sorted_tags: dict[str, list[dict]],
    model: str = OPENAI_MODEL,
) -> str:
    """Call OpenAI for each tag group and return a complete HTML document."""
    total_segments = len(sorted_tags)
    content_parts: list[str] = []
    previous_segment = ""

    for index, (tag, docs) in enumerate(sorted_tags.items(), start=1):
        logger.info("Generating segment %d/%d: %s (%d articles)", index, total_segments, tag, len(docs))

        segment_header = (
            f"\n<h1>Segment: {tag}</h1>"
            f"<p><i>Based on {len(docs)} articles</i>.</p>\n"
        )

        article_data = [
            {
                "title": d["title"],
                "author": d["author"],
                "tags": d["tags"],
                "summary": d["summary"],
                "site_name": d["site_name"],
                "source_url": d.get("source_url"),
                "image_url": d.get("image_url"),
                "published_date": d.get("published_date"),
                "number_from_this_site": d.get("number_from_this_site"),
            }
            for d in docs
        ]

        prompt = html_segment_prompt(
            tag=tag,
            index=index,
            total_segments=total_segments,
            articles=article_data,
            previous_segment=previous_segment,
            segment_header=segment_header,
        )

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )

        segment = segment_header + response.choices[0].message.content
        content_parts.append(segment)
        previous_segment = segment

    body = "".join(content_parts)
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
