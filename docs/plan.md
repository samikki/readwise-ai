# readwise-ai — Refactoring & Feature Plan

## Overview

Full refactor of the original monolithic scripts into a clean, maintainable codebase, with GitHub setup and taste-profile-aware summarisation.

---

## Phase 1 — GitHub & project hygiene

**Goal:** Get the project into a proper state before touching logic.

- [x] Initialise git repo
- [x] Create `.gitignore` — excludes `.env`, profile files, `__pycache__`, etc.
- [x] Create `README.md` covering: what it does, setup, usage, configuration
- [x] Move secrets to `.env.example` (template with empty values, safe to commit)
- [x] Push to GitHub

---

## Phase 2 — Refactor into modules

**Goal:** Replace two monolithic scripts with a clean package structure.

### Target structure

```
readwise-ai/
├── readwise_ai/
│   ├── __init__.py
│   ├── config.py          # All configuration: tags, model, defaults
│   ├── readwise.py        # Readwise API client (fetch + save + delete)
│   ├── openai_client.py   # OpenAI wrapper
│   ├── summariser.py      # Core summarisation logic
│   └── taste_profile.py   # Profile loader and prompt renderer
├── templates/
│   ├── prompt_template.md       # Main briefing prompt with $variables
│   └── watch_prompt_template.md # Short watch summary prompt
├── build.py               # Entry point: full briefing or watch summary
├── sync_profile.py        # Sync taste_profile.md from an external source
├── debug_fetch.py         # Diagnostic: show what articles would be fetched
├── config.toml            # User-editable settings
├── taste_profile.example.md
├── local_profile.example.md
├── docs/
│   └── plan.md
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

### Specific tasks

- [x] Extract Readwise API calls into `readwise.py`
- [x] Extract OpenAI client into `openai_client.py`
- [x] Move all configuration into `config.py` (loaded from `config.toml`)
- [x] Move prompt template into editable `prompt_template.md`
- [x] Add type hints throughout
- [x] Replace `print()` with `logging`
- [x] Make model configurable via `config.toml`

---

## Phase 3 — Taste profile integration

**Goal:** Make summaries feel like they were written for a specific reader, not a generic audience.

The taste profile lives in `taste_profile.md` (gitignored). Copy from `taste_profile.example.md`
and fill it in with your intellectual interests, reading personality, and priorities.
Optionally sync it from an external source (e.g. Obsidian) using `sync_profile.py`.

A local addendum in `local_profile.md` lets you specify geographic focus, product interests,
reading weights, and editorial tone without touching the main profile.

### What was changed

- [x] Single OpenAI call generates one unified briefing article (not per-tag segments)
- [x] Model decides structure and depth based on the taste profile
- [x] `★ SIGNAL` callouts for content particularly worth the reader's attention
- [x] Language configurable (`config.toml → [output] → language`)
- [x] Readwise Reader deep links used for article links

---

## Phase 4 — Quality of life improvements

- [x] Add `--dry-run` flag: generate summary but don't post to Readwise
- [x] Add `--output` flag: save summary to a local file
- [x] Add `--max-articles` flag
- [x] Auto-delete old AI-generated summaries from Readwise (configurable retention)
- [x] Cron setup with dated log files and auto-cleanup of old logs
- [x] Multi-source fetching with deduplication (`feed` + `later`)
- [ ] Better error messages when API calls fail
- [ ] Add `--since` flag to override the time window from the command line

---

## Notes

- Summaries are identified in Readwise by the `summary_url_prefix` set in `config.toml`.
  Use a URL on a domain you own — it is never fetched, only used as a unique identifier.
- The `local_profile.md` addendum is designed for things that change more often than the
  core profile: current location priorities, a car you own, a project you're tracking, etc.
