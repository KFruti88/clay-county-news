import json
from datetime import datetime
import os

# 1. Load your JSON data safely
try:
    with open('news_data.json', 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Error: news_data.json not found")
    exit(1)
except json.JSONDecodeError:
    print("Error: news_data.json is not valid JSON")
    exit(1)

rss_items = ""

# 2. Process the data
# This handles both lists of text AND lists of objects
for item in data:
    if isinstance(item, dict):
        # Format: {"title": "Example", "link": "...", "description": "..."}
        title = item.get('title', 'No Title')
        link = item.get('link', 'https://github.com/KFruti88/clay-county-news')
        desc = item.get('description', 'No description provided.')
    else:
        # Format: ["Headline 1", "Headline 2"]
        title = str(item)
        link = 'https://github.com/KFruti88/clay-county-news'
        desc = 'Update from news_data.json'

    # Build the XML item string
    rss_items += f"""
        <item>
            <title>{title}</title>
            <link>{link}</link>
            <description>{desc}</description>
            <pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
        </item>"""

# 3. Create the full RSS structure
rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
    <channel>
        <title>Clay County News Feed</title>
        <link>https://github.com/KFruti88/clay-county-news</link>
        <description>Latest updates from news_data.json</description>
        {rss_items}
    </channel>
</rss>"""

# 4. Save the file
with open('feed.xml', 'w') as f:
    f.write(rss_feed)
    print("Successfully generated feed.xml")
