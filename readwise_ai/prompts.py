import json


def html_segment_prompt(
    tag: str,
    index: int,
    total_segments: int,
    articles: list[dict],
    previous_segment: str,
    segment_header: str,
) -> str:
    n = len(articles)
    return f"""
You are creating an article which summarizes the content of a newsfeed.
This is one segment of it and will be later included in the actual article.
It is segment {index} out of {total_segments}.
The topic of this segment is about {tag}.
Include content from every {n} articles in the newsfeed, mentioning each at least once in a dedicated bullet or paragraph.

Keep the text easy-to-glance and informative.
The user should understand what is being talked about based on the information you provide.
The script's main purpose is to help reader quickly learn about news with the subject {tag}.
Summaries must be based solely on the supplied newsfeed content. Do not invent or guess.
Use all the tricks you know to make it interesting and entertaining.
Highlight surprising and fun details when possible.

Articles that have variable number_from_this_site value at 1 should have stronger emphasis, but do not omit any others.
Utilize the article summaries to find interesting information and use it to guide the script.
If possible, find a common theme or topic from all the articles and use it to guide the allover story.
This will be read on the screen on computer or mobile device.
Do not add images to the summary.

Format the summary in a natural, conversational style
that flows well when spoken aloud. Use clear, engaging
language with smooth transitions, avoid dense or
overly formal phrasing, and structure sentences to be
easy to follow when listened to rather than read.

You can provide links to the original article but
ensure that links are integrated naturally within the
text so they make sense when spoken aloud. Instead of
generic phrases like 'check out the details here,'
incorporate the source naturally such as using the main
point of the summary as a link text.

The snippet will be concatenated to other segments so there should be no headers or footers.
Do not use code fences (```). Provide only a plain HTML snippet.
All opened HTML tags must be properly closed.
Do not include <html>, <body>, or any headers/footers. Only provide the snippet.
No images or additional styling should be included.
Use only of minimal tags like <p>, <ul>, <li>, <strong>, <a>, etc.
Ensure your HTML is valid and does not break when joined with other segments.
Segment title is already added as h1 so you do not need to add it.
You can insert subtitles with h2 or h3 if suitable.

Here is the newsfeed for topic {tag}:
--------------
{json.dumps(articles)}
--------------

Here is the previous segment. Use it only for context and style continuity. Do not repeat its text.
Continue naturally from the previous segment but avoid duplicated paragraphs.
--------------
{previous_segment}
--------------

Here is the beginning of this segment so far. You do not need to repeat it. Your answer will be appended to it.
--------------
{segment_header}
--------------
"""


def podcast_segment_prompt(
    tag: str,
    index: int,
    total_segments: int,
    articles: list[dict],
    previous_segment: str,
    segment_header: str,
) -> str:
    return f"""
You are creating a script for a podcast which will be generated with a TTS engine.
This is one segment of it and will be later included in the actual script.
The segment is about {tag} and it deals with the newsfeed I will give you below.

The podcast will have two hosts: Frasier and Niles.
The script is a discussion between these hosts about the articles in the newsfeed.
Format the script in JSON so that each line of either host is a separate element.
The JSON should include:
- host
- line: the line of text
- style: instructions to text-to-speech engine how this line should be spoken

Do not overuse the verbal trickery. The hosts do not need to repeat each other's names.
Use the names only when it is natural to do so.

Format the discussion in a natural, conversational style, like a radio morning show
that flows well when spoken aloud. Use clear, engaging
language with smooth transitions, avoid dense or
overly formal phrasing, and structure sentences to be
easy to follow when listened to rather than read.

Create a coherent segment that combines the articles in a natural way.
Articles that have variable number_from_this_site value at 1 should have stronger emphasis.
Utilize the article summaries to find interesting information and use it to guide the script.
If possible, find a common theme or topic from all the articles and use it to guide the overall story.
You can create an interesting discussion based on multiple articles about the common topic.

Everything should be suitable to be spoken aloud so no HTML, links, domain names, etc.
The script for the part should produce about a 5-minute long segment.

The snippet will be concatenated to other segments so there should be no headers or footers.
Do not use code fences (```). Provide only the discussion in JSON.
Segment title is already added so you do not need to add it.

Here is the newsfeed for topic {tag}:
--------------
{json.dumps(articles)}
--------------

Here is the previous segment. Use it only for context and style continuity. Do not repeat its text.
--------------
{previous_segment}
--------------

Here is the beginning of this segment so far. You do not need to repeat it. Your answer will be appended to it.
--------------
{segment_header}
--------------
"""
