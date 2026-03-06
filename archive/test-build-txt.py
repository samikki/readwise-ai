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

def fetch_reader_document_list_api(updated_after=None, location=None, limit=5):
    import time
    full_data = []
    next_page_cursor = None
    max_retries = 5
    
    # Only fetch one page with up to 'limit' results
    params = {}
    if updated_after:
        params['updatedAfter'] = updated_after
    if location:
        params['location'] = location
    
    # Implement retry logic with proper rate limit handling
    retry_count = 0
    while retry_count < max_retries:
        response = requests.get(
            url="https://readwise.io/api/v3/list/",
            params=params,
            headers={"Authorization": f"Token {readwise_token}"}
        )
        
        if response.status_code == 200:
            # Success - process the data
            response_data = response.json()
            # Only take up to 'limit' results
            full_data.extend(response_data['results'][:limit])
            break
        elif response.status_code == 429:
            # Rate limited - use Retry-After header if available
            retry_count += 1
            if retry_count < max_retries:
                # Get retry delay from header or use default exponential backoff
                if 'Retry-After' in response.headers:
                    delay = int(response.headers['Retry-After'])
                    print(f"Rate limited (429). API requested wait time: {delay} seconds (Attempt {retry_count}/{max_retries})")
                else:
                    # Fallback to exponential backoff if header not present
                    delay = 10 * (2 ** (retry_count - 1))  # Start with 10 seconds
                    print(f"Rate limited (429). Using backoff delay: {delay} seconds (Attempt {retry_count}/{max_retries})")
                
                time.sleep(delay)
            else:
                print(f"Failed after {max_retries} retries due to rate limiting.")
                return full_data
        else:
            # Other error
            print(f"Error: {response.status_code} - {response.text}")
            return full_data
            
    return full_data

# Fetch documents - limit to 5 articles
docs_after_date = datetime.now() - timedelta(days=args.days)  # use the provided days
new_data = fetch_reader_document_list_api(docs_after_date.isoformat(), args.source, limit=5)

print(f"Fetched {len(new_data)} articles from the API")

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
    
    # Add number_from_this_site to each document
    for doc in new_data:
        doc['number_from_this_site'] = site_name_count[doc['site_name']]
    
    # Filter out documents with tags in ignore_tags
    filtered_data = [
        {
            'title': doc['title'],
            'author': doc['author'],
            'tags': doc['tags'],
            'summary': doc['summary'],
            'site_name': doc['site_name'],
            'url': doc['url'],
            'number_from_this_site': doc['number_from_this_site']
        }
        for doc in new_data
        if not any(tag in ignore_tags for tag in doc.get('tags', []))  # Use ignore_tags variable
    ]
else:
    print("Unexpected data structure:", new_data)
    filtered_data = []

print(f"After filtering, {len(filtered_data)} articles remain")

# create a different json variable for each tag
tags = {}
for doc in filtered_data:
    for tag in doc['tags']:
        if tag not in tags:
            tags[tag] = []
        tags[tag].append(doc)

# Sort tags by priority
sorted_tags = {}
for tag in priority_tags:
    if tag in tags:
        sorted_tags[tag] = tags[tag]

# Add any remaining tags
for tag in tags:
    if tag not in sorted_tags and tag not in ignore_tags:
        sorted_tags[tag] = tags[tag]

# Count the total number of segments
total_segments = len(sorted_tags)
print(f"\nProcessing {total_segments} segments based on {len(filtered_data)} articles")

# Initialize content script
content_script = ""
previous_segment = ""

# Go through each segment
for index, (tag, docs) in enumerate(sorted_tags.items(), start=1):  # Start counting from 1
    number_of_tags = len(docs)
    print(f"\nProcessing segment {index}/{total_segments}: {tag} with {number_of_tags} articles")

    this_data = []
    for doc in docs:
        this_data.append({
            "title": doc['title'],
            "author": doc['author'],
            "tags": doc['tags'],
            "summary": doc['summary'],
            "site_name": doc['site_name'],
            "url": doc['url'],
            "number_from_this_site": doc['number_from_this_site']
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

# Wrap the content in HTML tags
content_script = "<html><body>" + content_script + "</body></html>"

# Print the generated summary
print("\n===== GENERATED AI SUMMARY =====\n")
print(content_script)
print("\nTest completed. No data was sent to Readwise.")
