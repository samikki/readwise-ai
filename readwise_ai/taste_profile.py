import logging
from pathlib import Path
from string import Template

logger = logging.getLogger(__name__)

_PROFILE_PATH = Path("taste_profile.md")
_LOCAL_PROFILE_PATH = Path("local_profile.md")
_TEMPLATE_PATH = Path("templates/prompt_template.md")


def load_profile() -> str:
    if not _PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"{_PROFILE_PATH} not found — run: python sync_profile.py"
        )
    return _PROFILE_PATH.read_text(encoding="utf-8")


def load_local_profile() -> str:
    """Load the local addendum profile. Returns empty string if file is absent."""
    if not _LOCAL_PROFILE_PATH.exists():
        logger.debug("local_profile.md not found — skipping addendum")
        return ""
    return _LOCAL_PROFILE_PATH.read_text(encoding="utf-8").strip()


def load_template() -> str:
    if not _TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"{_TEMPLATE_PATH} not found")
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def render_prompt(
    *,
    n_articles: int,
    articles_json: str,
    language: str,
    template_path: Path | None = None,
) -> str:
    """Load profile + template from disk and render the final prompt.

    Args:
        template_path: Override the default prompt template. When None,
            uses templates/prompt_template.md (existing behaviour).
    """
    local = load_local_profile()
    local_block = f"\n\n---\n\n{local}" if local else ""
    path = template_path or _TEMPLATE_PATH
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    template_text = path.read_text(encoding="utf-8")
    return Template(template_text).substitute(
        taste_profile=load_profile(),
        local_profile=local_block,
        n_articles=n_articles,
        articles_json=articles_json,
        language=language,
    )
