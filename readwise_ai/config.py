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

PRIORITY_TAGS: list[str] = _cfg["tags"]["priority"]
IGNORE_TAGS: list[str] = _cfg["tags"]["ignore"]

OUTPUT_LANGUAGE: str = _cfg["output"]["language"]

TASTE_PROFILE_SOURCE: str = _cfg["profile"]["source"]
