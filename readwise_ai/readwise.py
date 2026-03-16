import logging
import time
from typing import Optional

import requests

from .config import READWISE_TOKEN

logger = logging.getLogger(__name__)

_LIST_URL = "https://readwise.io/api/v3/list/"
_SAVE_URL = "https://readwise.io/api/v3/save/"
_DELETE_URL = "https://readwise.io/api/v3/delete/"
_MAX_RETRIES = 5


def _get_with_retry(url: str, params: dict) -> Optional[requests.Response]:
    """GET with exponential back-off on 429."""
    for attempt in range(1, _MAX_RETRIES + 1):
        response = requests.get(
            url=url,
            params=params,
            headers={"Authorization": f"Token {READWISE_TOKEN}"},
        )
        if response.status_code == 200:
            return response
        if response.status_code == 429:
            if attempt == _MAX_RETRIES:
                logger.error("Rate-limited: giving up after %d retries", _MAX_RETRIES)
                return None
            delay = int(response.headers.get("Retry-After", 10 * (2 ** (attempt - 1))))
            logger.warning(
                "Rate-limited (429). Waiting %ds (attempt %d/%d)", delay, attempt, _MAX_RETRIES
            )
            time.sleep(delay)
        else:
            logger.error("API error %d: %s", response.status_code, response.text)
            return None
    return None


def fetch_documents(
    updated_after: Optional[str] = None,
    location: Optional[str] = None,
) -> list[dict]:
    """Fetch all documents from Readwise Reader, handling pagination."""
    full_data: list[dict] = []
    next_page_cursor: Optional[str] = None

    while True:
        params: dict = {}
        if next_page_cursor:
            params["pageCursor"] = next_page_cursor
        if updated_after:
            params["updatedAfter"] = updated_after
        if location:
            params["location"] = location

        response = _get_with_retry(_LIST_URL, params)
        if response is None:
            break

        data = response.json()
        full_data.extend(data["results"])
        next_page_cursor = data.get("nextPageCursor")
        if not next_page_cursor:
            break

    logger.info("Fetched %d documents total", len(full_data))
    return full_data


def save_document(content: dict) -> bool:
    """Post a document to Readwise. Returns True on success."""
    response = requests.post(
        url=_SAVE_URL,
        headers={"Authorization": f"Token {READWISE_TOKEN}"},
        json=content,
    )
    if response.status_code == 201:
        logger.info("Saved document: %s", content.get("title"))
        return True
    logger.error("Failed to save: %d %s", response.status_code, response.text)
    return False


_BOOKS_URL = "https://readwise.io/api/v2/books/"


def fetch_highlighted_urls(url_prefix: str) -> set[str]:
    """Return source_urls of documents matching url_prefix that have highlights.

    Uses the Readwise v2 export API which exposes num_highlights per book.
    """
    highlighted: set[str] = set()
    page = 1
    while True:
        response = requests.get(
            url=_BOOKS_URL,
            headers={"Authorization": f"Token {READWISE_TOKEN}"},
            params={"page_size": 100, "page": page, "category": "articles"},
        )
        if response.status_code != 200:
            logger.warning("v2 books API error %d — skipping highlight check", response.status_code)
            return highlighted
        data = response.json()
        for book in data.get("results", []):
            source_url = book.get("source_url") or ""
            if source_url.startswith(url_prefix) and book.get("num_highlights", 0) > 0:
                highlighted.add(source_url)
        if not data.get("next"):
            break
        page += 1
    logger.info("Found %d highlighted summaries matching %s", len(highlighted), url_prefix)
    return highlighted


def delete_document(doc_id: str) -> bool:
    """Delete a document from Readwise Reader by ID. Returns True on success."""
    response = requests.delete(
        url=f"{_DELETE_URL}{doc_id}/",
        headers={"Authorization": f"Token {READWISE_TOKEN}"},
    )
    if response.status_code in (200, 204):
        logger.info("Deleted document: %s", doc_id)
        return True
    logger.error("Failed to delete %s: %d %s", doc_id, response.status_code, response.text)
    return False
