# readwise-ai — Refactoring & Feature Plan

## Overview

Full refactor of the original monolithic scripts into a clean, maintainable codebase, with GitHub setup and taste-profile-aware summarisation.

---

## Phase 1 — GitHub & project hygiene

**Goal:** Get the project into a proper state before touching logic.

- [ ] Initialise git repo (`git init`)
- [ ] Create `.gitignore` — must exclude `.env`, `__pycache__`, `*.pyc`, `.DS_Store`
- [ ] Create `README.md` covering: what it does, setup, usage, configuration
- [ ] Move secrets to `.env.example` (template with empty values, safe to commit)
- [ ] Verify `.env` is gitignored before first commit
- [ ] Push to GitHub (new private repo, name: `readwise-ai`)

---

## Phase 2 — Refactor into modules

**Goal:** Replace two monolithic scripts with a clean package structure.

### Target structure

```
readwise-ai/
├── readwise_ai/
│   ├── __init__.py
│   ├── config.py          # All configuration: tags, model, defaults
│   ├── readwise.py        # Readwise API client (fetch + save)
│   ├── openai_client.py   # OpenAI wrapper
│   ├── prompts.py         # All prompt templates
│   ├── summariser.py      # Core summarisation logic
│   └── podcast.py         # Podcast script generation logic
├── build.py               # Entry point: HTML summary
├── podcast.py             # Entry point: podcast script
├── docs/
│   └── plan.md
├── .env.example
├── .gitignore
├── README.md
├── CLAUDE.md
└── requirements.txt
```

### Specific tasks

- [ ] Extract `fetch_reader_document_list_api()` into `readwise.py` as a proper class or set of functions
- [ ] Extract `save_to_readwise()` into `readwise.py`
- [ ] Move all tag config (priority_tags, ignore_tags) into `config.py`
- [ ] Move all prompt strings into `prompts.py`
- [ ] Remove duplicated logic between `build-txt.py` and `test-build-txt.py` — shared code goes into modules
- [ ] Add type hints throughout
- [ ] Replace `print()` with `logging` (use `loguru` or stdlib `logging`)
- [ ] Fix model name — `gpt-4.5-preview` is not valid; use `gpt-4o` or make it configurable via `.env`

---

## Phase 3 — Taste profile integration

**Goal:** Make summaries feel like they were written for Sami specifically, not a generic reader.

Sami's taste profile lives at:
`/path/to/your/taste_profile_source.md`

### What to change

**In `prompts.py`**, update the system prompt to include Sami's intellectual context:

- He thinks in systems and frameworks — surface structural patterns across articles, not just individual takeaways
- Via negativa orientation — when relevant, note what's being ruled out or what to avoid, not just what's good
- Skeptical about AI hype — don't present AI developments uncritically; acknowledge tensions and open questions
- Appreciates wit and directness — write with a voice, not bland corporate neutrality
- Finnish lens — when relevant, connect to Finnish context or perspective
- Depth over breadth — if one article is significantly more substantial than others in a tag group, give it more space and say so explicitly

**Concrete prompt additions:**

```
The reader is a Finnish systems thinker who:
- Prefers frameworks and mental models over collections of facts
- Has a via negativa instinct: what should be avoided or ruled out matters as much as what's good
- Is an AI practitioner who follows developments critically — don't present AI news uncritically
- Appreciates a direct, opinionated voice over neutral summarisation
- Values depth: if one article is substantially richer than others, say so and give it more space
- Thinks in structural patterns across domains — surface connections between articles where genuine

Write for this specific reader. Don't write for a general audience.
```

- [ ] Add taste profile system prompt to HTML summary generator
- [ ] Add taste profile system prompt to podcast script generator (Frasier and Niles should reflect his sensibility, not generic NPR hosts)
- [ ] Add a "significance flag" — let the model call out when something is particularly worth Sami's attention given his profile
- [ ] Consider: load taste profile from file at runtime rather than hardcoding, so it stays in sync with updates

---

## Phase 4 — Quality of life improvements

- [ ] Add `--dry-run` flag: generate summary but don't post to Readwise
- [ ] Add `--output` flag: save summary to a local file as well
- [ ] Make model configurable via `.env` (`OPENAI_MODEL=gpt-4o`)
- [ ] Add `--tags` flag to filter to specific tags only
- [ ] Better error messages when API calls fail
- [ ] Consider: scheduled run via cron or launchd on Mac

---

## Notes

- The original `test-build-txt.py` podcast mode is worth keeping — it's a genuinely interesting output format. Just needs cleanup and taste profile integration.
- The Frasier/Niles persona for the podcast is charming but could be more Sami-specific. Consider making the hosts' perspective align with his taste profile rather than a generic witty-intellectual tone.
- Long term: consider whether the taste profile should be loaded dynamically from the Obsidian file so changes to it automatically flow through to summaries.
