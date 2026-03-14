import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

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
WATCH_URL_PREFIX: str = _watch.get("watch_url_prefix", "https://pinseri.fi/readwise-ai/watch/")
WATCH_KEEP: int = _watch.get("keep", 3)
