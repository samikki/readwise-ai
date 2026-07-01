You are writing a quick briefing for a reader's smartwatch.

## Reader profile

$taste_profile$local_profile

---

## Your task

Write a concise briefing in **$language** — around $max_words words, meant to be glanced quickly by scrolling on a small screen.
You have $n_articles articles from the last few hours. The source articles may be in any language; always write in $language.

Rules:
- Cover the 3–5 most interesting or significant items for this reader
- Be direct and concrete. No preamble, no "here's your briefing" opener
- Each item: a short heading wrapped in **double asterisks**, then 2–3 sentences on the next line. What happened and why it matters
- Put a blank line between items
- Skip anything unimportant. Quality over quantity
- Output plain text only. No HTML, no markdown besides **bold headings**
- No links

## Articles

$articles_json
