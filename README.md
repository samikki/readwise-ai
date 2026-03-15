# readwise-ai  ·  v1.1

Fetches articles from your [Readwise Reader](https://readwise.io/read) library, generates an AI-powered daily briefing shaped by your personal taste profile, and saves it back to Readwise as an article. Optionally generates a short watch summary (for an Apple Watch companion app).

## How it works

1. Fetches articles from Readwise Reader (feed, new, or both)
2. Filters and prioritises them by your tag preferences
3. Sends them to an OpenAI model with your taste profile as context
4. Saves the generated briefing back to Readwise as a new article

The daily briefing is a longer editorial summary. The watch summary is a short (~200 word) version of the last few hours, designed for quick glancing.

## Requirements

- Python 3.11+
- A **paid** [Readwise](https://readwise.io) subscription with Reader access (Ghostreader custom prompts require a paid plan)
- An [OpenAI](https://platform.openai.com) API key (see below)

## OpenAI API key and costs

This tool uses the OpenAI API directly with your own key — it does **not** use the Readwise-provided AI model. This means you pay OpenAI separately for every run.

### Getting an API key

1. Create an account at [platform.openai.com](https://platform.openai.com)
2. Go to **API keys** and create a new secret key
3. Add billing details and set a monthly spend limit (recommended — easy to forget it's running)
4. Paste the key into your `.env` file as `OPENAI_API_KEY`

### Token usage estimates

The tool is prompt-heavy. Both your taste profile and the full article list are sent on every call. Rough per-run estimates with default settings (`max_articles = 100`, watch every 3 hours):

| Run type | Typical input | Output | Total |
|---|---|---|---|
| Daily briefing (×1/day) | 12,000–30,000 tokens | ~2,000 tokens | ~14,000–32,000 |
| Watch summary (×8/day) | 5,000–8,000 tokens | ~400 tokens | ~5,500–8,500 |
| **Daily total** | | | **~60,000–100,000 tokens** |
| **Monthly total** | | | **~1.8M–3M tokens** |

Input tokens dominate — the article summaries and your taste profile are the main driver. Reducing `max_articles` in `config.toml` is the most effective way to cut costs.

### Model choice: quality vs. cost

The model is set in `config.toml` under `[openai] model`. This is the single biggest lever on both output quality and cost.

| Model tier | Quality | Relative cost | Notes |
|---|---|---|---|
| GPT-5 mini variants | Good | Low | Fine for the watch summary; briefing quality noticeably lower |
| GPT-5 standard | Very good | Medium | Solid default for most users |
| GPT-5 premium variants | Excellent | High | Meaningfully better editorial quality and cross-topic synthesis; cost scales sharply |

Check [OpenAI's pricing page](https://openai.com/api/pricing/) for current model names and rates — the lineup evolves quickly. Set a monthly spend cap in your OpenAI account settings if you run this on a schedule.

> **Tip:** You can use different models for different runs. The watch summary is short and tolerates a cheaper model well. Reserve a premium model for the daily briefing if cost is a concern.

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

### Set up Ghostreader in Readwise

This tool feeds article **summaries** and **tags** from your Readwise library directly into the LLM prompt. If those fields are empty, the briefing LLM has nothing but a title to work from — quality suffers significantly.

The recommended way to populate them automatically is Readwise Reader's **Ghostreader** feature, which runs a custom AI prompt on every article you save. To configure it: open [read.readwise.io](https://read.readwise.io), go to **Settings → Ghostreader**, and set up custom prompts for *Document summary* and *Auto-tag*.

You need two prompts:

---

**1. Document summary prompt** — runs on every new article and populates the summary field.

Ghostreader prompts use Jinja2-style template variables. A starting point:

```
You are a concise summariser. Your goal is to give me the key information from this article in as few words as possible.

Rules:
- First sentence: the single most important takeaway, or a direct answer if the title is a question or teaser.
- Follow with 2–3 sentences covering other essential points.
- No preamble. Never start with "This article" or "The author". No filler.
- If the article is behind a paywall or the content is missing, start your summary with [P].
- Write in present tense. Aim for 100–150 words maximum.

Title: {{ document.title }}
Author: {{ document.author }}

{% if (document.content | count_tokens) > 6000 %}
{{ document.content | central_sentences | join('\n\n') }}
{% else %}
{{ document.content }}
{% endif %}
```

Adapt the output language to match your preference (e.g., add "Always write in Finnish." if that's your reading language).

---

**2. Auto-tag prompt** — runs on every new article and assigns it a topic tag.

Design a flat taxonomy that matches your interests. Keep categories at the same level of specificity — mixing broad and narrow (e.g., "Technology" alongside "AI") causes the model to default to the broader one. A starting point:

```
Categorise this article into exactly one of the following topics:

AI: Artificial intelligence, machine learning, LLMs, and AI tools and research.
Technology: Software, hardware, cybersecurity, programming, and tech industry news not primarily about AI.
Science: Physics, biology, mathematics, astronomy, medicine, and scientific research.
Business: Companies, economics, investing, markets, and professional strategy.
Politics & Society: Government, policy, geopolitics, and social issues.
Health: Physical and mental health, nutrition, fitness, and medicine.
Arts & Culture: Literature, music, film, art, and cultural commentary.
Productivity: Personal organisation, note-taking, time management, and self-improvement.
Entertainment: Humour, games, TV, sports, and light content.
Other: Anything that does not fit the above categories.

Return only the category name. No explanation, no punctuation.

Title: {{ document.title }}
Author: {{ document.author }}

{% if (document.content | count_tokens) > 2000 %}
{{ document.content | central_sentences | join('\n\n') }}
{% else %}
{{ document.content }}
{% endif %}
```

Customise the taxonomy to your own interests — the example above is generic. Once you have your tags defined, update `IGNORE_TAGS` in `config.toml` to filter out any categories you never want to appear in your briefing.

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
