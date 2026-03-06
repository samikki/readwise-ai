import logging

from .config import OPENAI_MODEL
from .openai_client import client
from .prompts import podcast_segment_prompt

logger = logging.getLogger(__name__)


def generate_podcast_script(
    sorted_tags: dict[str, list[dict]],
    model: str = OPENAI_MODEL,
) -> str:
    """Call OpenAI for each tag group and return the full podcast script."""
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
                "url": d.get("source_url"),
                "number_from_this_site": d.get("number_from_this_site"),
            }
            for d in docs
        ]

        prompt = podcast_segment_prompt(
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

    return "<html><body>" + "".join(content_parts) + "</body></html>"
