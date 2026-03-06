from datetime import datetime, timedelta
import requests  
import json
import os
from dotenv import load_dotenv
import argparse
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

readwise_token = os.getenv("READWISE_TOKEN")

# Set up argument parsing
parser = argparse.ArgumentParser(description='Fetch documents from Readwise API.')
parser.add_argument('--source', type=str, default='feed', choices=['new', 'later', 'shortlist', 'archive', 'feed'],
                    help='Source from which to fetch documents (default: feed)')
parser.add_argument('--days', type=int, default=1, help='Number of days from the past to fetch documents (default: 1)')
args = parser.parse_args()

# Define the priority tags and ignore tags at the beginning
priority_tags = ["Local", "Tesla", "AI", "Movies", "TV", "Games", "Technology"]
ignore_tags = ["Humour", "Summary"]

def fetch_reader_document_list_api(updated_after=None, location=None):
    import time
    full_data = []
    next_page_cursor = None
    max_retries = 5
    
    while True:
        params = {}
        if next_page_cursor:
            params['pageCursor'] = next_page_cursor
        if updated_after:
            params['updatedAfter'] = updated_after
        if location:
            params['location'] = location
        # Debug message removed
        
        # Implement retry logic with proper rate limit handling
        retry_count = 0
        while retry_count < max_retries:
            response = requests.get(
                url="https://readwise.io/api/v3/list/",
                params=params,
                headers={"Authorization": f"Token {readwise_token}"}
            )
            
            # Debug message removed
            
            if response.status_code == 200:
                # Success - process the data
                response_data = response.json()
                full_data.extend(response_data['results'])
                next_page_cursor = response_data.get('nextPageCursor')
                break
            elif response.status_code == 429:
                # Rate limited - use Retry-After header if available
                retry_count += 1
                if retry_count < max_retries:
                    # Get retry delay from header or use default exponential backoff
                    if 'Retry-After' in response.headers:
                        delay = int(response.headers['Retry-After'])
                        # Keep error message for rate limiting
                        print(f"Rate limited (429). API requested wait time: {delay} seconds (Attempt {retry_count}/{max_retries})")
                    else:
                        # Fallback to exponential backoff if header not present
                        delay = 10 * (2 ** (retry_count - 1))  # Start with 10 seconds
                        # Keep error message for rate limiting
                        print(f"Rate limited (429). Using backoff delay: {delay} seconds (Attempt {retry_count}/{max_retries})")
                    
                    time.sleep(delay)
                else:
                    print(f"Failed after {max_retries} retries due to rate limiting.")
                    return full_data
            else:
                # Other error
                print(f"Error: {response.status_code} - {response.text}")
                return full_data
        
        # Break the outer loop if we've processed all pages
        if not next_page_cursor:
            break
            
    return full_data

# Fetch documents
docs_after_date = datetime.now() - timedelta(days=args.days)  # use the provided days
new_data = fetch_reader_document_list_api(docs_after_date.isoformat(), args.source)

if isinstance(new_data, list) and all(isinstance(doc, dict) for doc in new_data):
    new_data = [doc for doc in new_data if doc['reading_progress'] < 2]
    
    # Step 1: Count occurrences of each site_name
    site_name_count = {}
    for doc in new_data:
        site_name = doc['site_name']
        if site_name in site_name_count:
            site_name_count[site_name] += 1
        else:
            site_name_count[site_name] = 1

    # Step 2: Add the count to each document
    new_data = [
        {
            'title': doc['title'],
            'author': doc['author'],
            'tags': [tag['name'] for tag in doc['tags'].values()] if isinstance(doc['tags'], dict) else [],
            'summary': doc['summary'],
            'site_name': doc['site_name'],
            'source_url': doc.get('source_url'),
            'image_url': doc.get('image_url'),
            'published_date': doc.get('published_date'),
            'number_from_this_site': site_name_count[doc['site_name']]  # Add the count here
        }
        for doc in new_data
        if not any(tag in ignore_tags for tag in doc.get('tags', []))  # Use ignore_tags variable
    ]
else:
    print("Unexpected data structure:", new_data)

# count how many articles there are in the new_data
# print("There are " + str(len(new_data)) + " articles in the new_data")

# create a different json variable for each tag
tags = {}
for doc in new_data:
    for tag in doc['tags']:
        if tag not in tags:
            tags[tag] = []
        tags[tag].append(doc)

# Filter out ignore_tags from the tags dictionary
filtered_tags = {tag: docs for tag, docs in tags.items() if tag not in ignore_tags}
# Sort the tags, prioritizing the specified tags in the defined order
sorted_tags = {k: v for k, v in sorted(filtered_tags.items(), key=lambda item: (priority_tags.index(item[0]) if item[0] in priority_tags else len(priority_tags), item[0]))}

content_script = ""
previous_segment = ""

# Count the total number of segments
total_segments = len(sorted_tags)


# Go through each segment
for index, (tag, docs) in enumerate(sorted_tags.items(), start=1):  # Start counting from 1
    number_of_tags = len(docs)
#    print(f"Segment: {tag}")
#    print(f"Segment number in series: {index} out of {total_segments}")

    this_data = []
    for doc in docs:
        this_data.append({
            "title": doc['title'],
            "author": doc['author'],
            "tags": doc['tags'],
            "summary": doc['summary'],
            "site_name": doc['site_name'],
            "source_url": doc.get('source_url'),
            "image_url": doc.get('image_url'),
            "published_date": doc.get('published_date'),
            "number_from_this_site": doc.get('number_from_this_site')
        })
    number_of_articles_in_segment = len(this_data)
    this_segment = ""
    this_segment +="\n<h1>Segment: " + tag + "</h1><p><i>Based on " + str(number_of_articles_in_segment) + " articles</i>.</p>\n"  

    response = client.chat.completions.create(
        model="gpt-4.5-preview",
        messages=[
            {
                "role": "user",
                "content": f"""
                You are creating an article which summarizes the content of a newsfeed.
                This is one segment of it and will be later included in the actual article.
                It is segment {index} out of {total_segments}.
                The topic of this segment is about {tag}.
                Include content from every {number_of_articles_in_segment} articles in the newsfeed, mentioning each at least once in a dedicated bullet or paragraph. 

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
                generic phrases like ‘check out the details here,’
                incorporate the source naturally such as using the main
                point of the summary as a link text.

                The snippet will be concatenated to other segments so there should be no headers or footers.
                Do not use code fences (```). Provide only a plain HTML snippet.
                All opened HTML tags must be properly closed.
                Do not include <html>, <body>, or any headers/footers. Only provide the snippet.
                No images or additional styling should be included.
                Use only of minimal tags like <p>, <ul>, <li>, <strong>, <a>, etc.
                Ensure your HTML is valid and does not break when joined with other segments
                Segment title is already added as h1 so you do not need to add it.
                You can insert subtitles with h2 or h3 if suitable.

                Here is the newsfeed for topic {tag}:
                --------------
                {json.dumps(this_data)}
                --------------

                Here is the previous segment. Use it only for context and style continuity. Do not repeat its text.
                Continue naturally from the previous segment but avoid duplicated paragraphs.
                The final output must be a standalone snippet of valid HTML, even if it links thematically to the previous segment.
                --------------
                {previous_segment}
                --------------

                Here is the beginning of this segment so far. You do not need to repeat it. Your answer will be appended to it.
                --------------
                {this_segment}
                --------------
                """
            }
        ]
    )
    this_segment += response.choices[0].message.content
    content_script += this_segment
    previous_segment = this_segment

content_script = "<html><body>" + content_script + "</body></html>"

# create a json structure of the content with following variables
timestamp = datetime.now().isoformat()
# today's date in dd.mm.yyyy format
date_title = timestamp[:10].replace("-", ".")

content_json = {
    "url": "https://example.com/summary" + timestamp,
    "title": f"Feed summary on {date_title} from {args.source}",  # Include source in the title
    "should_clean_html": False,
    "html": content_script,
    "tags": ["Summary"],
    "published_date": timestamp,
    "location": "new",
    "saved_using": "AI summarizer",
    "author": "AI",
    "category": "article"
}

# post and get the returned status code
response = requests.post(
    url="https://readwise.io/api/v3/save/",
    headers={"Authorization": "Token " + readwise_token},
    json=content_json
)

if response.status_code == 201:
    # Success message removed
    pass
else:
    print("Failed to save content. Status code:", response.status_code)

# Print only the final response
print(response.json())
