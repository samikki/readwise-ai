# readwise-ai

Fetches articles from Readwise Reader, groups them by tag, generates AI summaries, and saves them back to Readwise.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in your tokens
```

## Usage

### HTML summary (posts to Readwise)

```bash
python build.py                        # last 24h from feed
python build.py --days 3 --source new  # last 3 days from "new"
python build.py --dry-run              # print output, don't post
python build.py --output summary.html  # also save to file
```

### Podcast script (Frasier & Niles, prints to stdout)

```bash
python podcast.py
python podcast.py --limit 5 --output script.html  # quick test, save to file
```

## Configuration

| Variable | Description |
|---|---|
| `READWISE_TOKEN` | Readwise API token |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_MODEL` | Model name (default: `gpt-4o`) |

## Structure

```
readwise_ai/
├── config.py        # env vars, tag lists
├── readwise.py      # Readwise API client
├── openai_client.py # OpenAI client
├── prompts.py       # prompt templates
├── summariser.py    # HTML summary logic
└── podcast.py       # podcast script logic
build.py             # entry point: HTML summary
podcast.py           # entry point: podcast script
archive/             # original monolithic scripts
```
