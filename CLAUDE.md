# readwise-ai — Claude Code Instructions

This project is an AI-powered Readwise summary generator. It fetches articles from Readwise Reader, generates a daily briefing article using an LLM shaped by a personal taste profile, and saves the result back to Readwise.

## Hard rules — never break these without explicit instruction

- **Never overwrite or reset a working file to "generic" or "example" values.** If a file needs a public-safe version for the repo, create a new `*.example.*` file alongside it. Leave the original untouched.
- **Never delete content from a file the user didn't ask you to change.** Changing one thing in a file does not give permission to restructure, clean up, or "improve" the rest of it.
- **Before deleting, resetting, or removing anything from git tracking, state exactly what will be lost and wait for confirmation.** This applies to `git rm`, overwriting files, and any destructive action.
- Never commit `.env`, `config.toml`, `taste_profile.md`, or `local_profile.md` — these are personal and gitignored.
- Never commit any API keys or secrets.

## File layout

| File | In git | Purpose |
|---|---|---|
| `.env` | No | API secrets — never committed |
| `.env.example` | Yes | Template for new users |
| `config.toml` | No | Your real settings — never committed |
| `config.example.toml` | Yes | Template with neutral defaults for new users |
| `taste_profile.md` | No | Your personal taste profile — never committed |
| `taste_profile.example.md` | Yes | Template and instructions for new users |
| `local_profile.md` | No | Your local priorities addendum — never committed |
| `local_profile.example.md` | Yes | Template and instructions for new users |

## Code rules

- All new code should have type hints
- Use standard `logging` — no bare `print()` in production code
- Target Python 3.11+

## Docs

- `docs/plan.md` — refactoring and feature roadmap
