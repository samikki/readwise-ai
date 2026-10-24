import logging
import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# --- Secrets from .env ---
READWISE_TOKEN: str = os.getenv("READWISE_TOKEN", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# --- Settings from config.toml ---
_CONFIG_PATH = Path(__file__).parent.parent / "config.toml"
with _CONFIG_PATH.open("rb") as _f:
    _cfg = tomllib.load(_f)

OPENAI_MODEL: str = _cfg["openai"]["model"]

DEFAULT_DAYS: int = _cfg["fetch"]["days"]
DEFAULT_SOURCES: list[str] = _cfg["fetch"]["sources"]
DEFAULT_MAX_ARTICLES: int = _cfg["fetch"]["max_articles"]
SUMMARY_RETENTION_DAYS: int = _cfg["fetch"]["summary_retention_days"]

IGNORE_TAGS: list[str] = _cfg["tags"]["ignore"]

OUTPUT_LANGUAGE: str = _cfg["output"]["language"]
SUMMARY_URL_PREFIX: str = _cfg["output"]["summary_url_prefix"]

READER_NAME: str = _cfg["profile"]["name"]
TASTE_PROFILE_SOURCE: str = _cfg["profile"]["source"]

# --- Watch summary settings (optional section, safe defaults) ---
_watch = _cfg.get("watch", {})
WATCH_HOURS: int = _watch.get("hours", 6)
WATCH_MAX_WORDS: int = _watch.get("max_words", 200)
WATCH_TAG: str = _watch.get("tag", "WatchSummary")
WATCH_URL_PREFIX: str = _watch.get("watch_url_prefix", "")
WATCH_KEEP: int = _watch.get("keep", 3)


# --- URL prefix validation ---
# Cleanup deletes documents whose URL starts with these prefixes. An empty or
# loose prefix would match the user's own articles, so cleanup refuses to run
# unless the prefix is an https:// URL with a host that ends with a slash.
def is_valid_url_prefix(prefix: str) -> bool:
    """Return True if prefix is safe to use for identifying generated documents."""
    if not isinstance(prefix, str) or not prefix.endswith("/"):
        return False
    if not prefix.startswith("https://"):
        return False
    host = prefix[len("https://"):].split("/", 1)[0]
    return bool(host)


SUMMARY_URL_PREFIX_VALID: bool = is_valid_url_prefix(SUMMARY_URL_PREFIX)
WATCH_URL_PREFIX_VALID: bool = is_valid_url_prefix(WATCH_URL_PREFIX)

if not SUMMARY_URL_PREFIX_VALID:
    logger.warning(
        "output.summary_url_prefix %r is invalid (must start with https:// and end with /) "
        "— summary cleanup is disabled",
        SUMMARY_URL_PREFIX,
    )
if not WATCH_URL_PREFIX_VALID:
    logger.warning(
        "watch.watch_url_prefix %r is invalid (must start with https:// and end with /) "
        "— watch cleanup is disabled",
        WATCH_URL_PREFIX,
    )
