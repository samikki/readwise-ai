import json
import logging
from pathlib import Path
from string import Template

logger = logging.getLogger(__name__)

_PROFILE_PATH = Path("taste_profile.md")
_TEMPLATE_PATH = Path("prompt_template.md")


def load_profile() -> str:
    if not _PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"{_PROFILE_PATH} not found — run: python sync_profile.py"
        )
    return _PROFILE_PATH.read_text(encoding="utf-8")


def load_template() -> str:
    if not _TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"{_TEMPLATE_PATH} not found")
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def render_prompt(*, n_articles: int, articles_json: str) -> str:
    """Load profile + template from disk and render the final prompt."""
    return Template(load_template()).substitute(
        taste_profile=load_profile(),
        n_articles=n_articles,
        articles_json=articles_json,
    )
