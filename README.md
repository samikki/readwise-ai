# readwise-ai

Fetches articles from your [Readwise Reader](https://readwise.io/read) library, generates an AI-powered daily briefing shaped by your personal taste profile, and saves it back to Readwise as an article. Optionally generates a short watch summary (for an Apple Watch companion app).

## How it works

1. Fetches articles from Readwise Reader (feed, new, or both)
2. Filters and prioritises them by your tag preferences
3. Sends them to an OpenAI model with your taste profile as context
4. Saves the generated briefing back to Readwise as a new article

The daily briefing is a longer editorial summary. The watch summary is a short (~200 word) version of the last few hours, designed for quick glancing.

## Requirements

- Python 3.11+
- A [Readwise](https://readwise.io) account with Reader
- An [OpenAI](https://platform.openai.com) API key

## Installation

```bash
git clone https://github.com/samikki/readwise-ai.git
cd readwise-ai

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure secrets

```bash
cp .env.example .env
```

Edit `.env` and fill in your tokens:

```
READWISE_TOKEN=your_readwise_token_here
OPENAI_API_KEY=your_openai_key_here
```

Your Readwise token is at [readwise.io/access_token](https://readwise.io/access_token).

### Configure settings

```bash
cp config.example.toml config.toml
```

Edit `config.toml` to set your name, preferred language, OpenAI model, tags to prioritise/ignore, and how many days of articles to fetch.

### Set up your taste profile

```bash
cp taste_profile.example.md taste_profile.md
cp local_profile.example.md local_profile.md
```

Edit these files to describe your reading interests and priorities. The taste profile is injected into the prompt — the more specific you are, the better the briefing.

## Usage

### Daily briefing

```bash
# Generate and post to Readwise
python build.py

# Last 3 days from "new" inbox
python build.py --days 3 --source new

# Dry run — print output, don't post
python build.py --dry-run

# Also save to a local file
python build.py --output summary.html
```

### Watch summary (short, last few hours)

```bash
python build.py --watch
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--days N` | 1 | How many days back to fetch articles |
| `--source` | `feed` | `feed`, `new`, or `all` |
| `--max-articles N` | 50 | Max articles to include in the prompt |
| `--dry-run` | off | Print output without posting to Readwise |
| `--output FILE` | — | Also save HTML to a local file |
| `--watch` | off | Generate short watch summary instead |

## Automating with cron

```bash
crontab -e
```

Add entries like:

```
# Daily briefing at 8 AM
0 8 * * * /path/to/readwise-ai/run_build.sh >> /path/to/readwise-ai/logs/build-$(date +\%Y-\%m-\%d).log 2>&1

# Watch summary every 3 hours
0 */3 * * * /path/to/readwise-ai/run_watch.sh >> /path/to/readwise-ai/logs/watch-$(date +\%Y-\%m-\%d).log 2>&1
```

Make sure the scripts are executable:

```bash
chmod +x run_build.sh run_watch.sh
```

## File layout

| File | In git | Purpose |
|---|---|---|
| `.env` | No | Your API tokens — never committed |
| `.env.example` | Yes | Template for new users |
| `config.toml` | No | Your settings — never committed |
| `config.example.toml` | Yes | Template with neutral defaults |
| `taste_profile.md` | No | Your personal taste profile — never committed |
| `taste_profile.example.md` | Yes | Template and instructions |
| `local_profile.md` | No | Optional local/contextual priorities — never committed |
| `local_profile.example.md` | Yes | Template and instructions |
| `prompt_template.md` | Yes | Prompt template for the daily briefing |
| `watch_prompt_template.md` | Yes | Prompt template for the watch summary |
| `build.py` | Yes | Main entry point |
| `run_build.sh` | Yes | Shell wrapper for cron |
| `run_watch.sh` | Yes | Shell wrapper for watch summary cron |

## Watch app

There is a companion Apple Watch app in [readwise-ai-watchapp](https://github.com/samikki/readwise-ai-watchapp) that fetches and displays the latest watch summary.
