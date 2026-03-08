# readwise-ai — Claude Code Instructions

This project is an AI-powered Readwise summary generator. It fetches articles from Readwise Reader, generates a daily briefing article using an LLM shaped by a personal taste profile, and saves the result back to Readwise.

## Key rules

- Never commit `.env` or any API keys
- Never commit `taste_profile.md` or `local_profile.md` — these are personal and gitignored
- Use `python-dotenv` for all secrets
- All new code should have type hints
- Use standard `logging` — no bare `print()` in production code
- Target Python 3.11+

## Configuration

- Secrets go in `.env` (see `.env.example`)
- User-editable settings go in `config.toml`
- The taste profile lives in `taste_profile.md` (gitignored, copy from `taste_profile.example.md`)
- The local addendum lives in `local_profile.md` (gitignored, copy from `local_profile.example.md`)

## Docs

- `docs/plan.md` — refactoring and feature roadmap
