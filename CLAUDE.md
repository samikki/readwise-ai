# readwise-ai — Claude Code Instructions

This project is an AI-powered Readwise summary generator. It fetches articles from Readwise Reader, groups them by tag, generates summaries using an LLM, and saves them back to Readwise.

## Owner

Sami (user@example.com). See `docs/plan.md` for the full refactoring roadmap.

## Current state

Two monolithic Python scripts (`build-txt.py`, `test-build-txt.py`) that work but need significant modernisation. See `docs/plan.md` for details.

## Goal

Refactor into a clean, modular codebase, set up GitHub, and integrate Sami's personal taste profile so summaries are framed through his specific intellectual lens rather than generic AI output.

## Taste profile

Sami's full taste profile is at:
`/path/to/your/taste_profile_source.md`

Read this before working on any prompt engineering tasks. The summary version: systems thinker, rationalist, AI practitioner (skeptical not credulous), Finnish, reads deeply, via negativa orientation, appreciates wit and directness.

## Key rules

- Never commit `.env` or any API keys
- Use `python-dotenv` for all secrets
- All new code should have type hints
- Use `loguru` or standard `logging` — no bare `print()` in production code
- Target Python 3.11+

## Docs

- `docs/plan.md` — full refactoring and feature roadmap
