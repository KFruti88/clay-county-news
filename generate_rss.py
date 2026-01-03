import json
from datetime import datetime
import os

# Load your JSON data
try:
    with open('news_data.json', 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Error: news_data.json not found")
    exit(1)

rss_items = ""

# Handle if the JSON is a single list of strings or a list of dictionaries
for item in data:
    if isinstance(item, dict):
        # If it's a dictionary like {"title": "...", "link": "..."}
        title = item.get('title', 'No Title')
        link = item.get('link', 'https://github.com/KFruti88/clay-county-news')
        desc = item.get('description', '')
    else:
        # If it's just a string ["News 1", "News 2"]
        title = str(item)
        link = 'https://github.com/KFruti88/clay-county-news'
        desc = 'New update in news_data.json'

    rss_items += f"""
        <item>
            <title>{title}</title>
            <link>{link}</link>
            <description>{desc}</description>
            <pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
        </item>"""

# Full RSS wrapper
rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
    <channel>
        <title>Clay County News Feed</title>
        <link>https://github.com/KFruti88/clay-county-news</link>
        <description>Latest updates from news_data.json</description>
        {rss_items}
    </channel>
</rss>"""

with open('feed.xml', 'w') as f:
    f.write(rss_feed)
    print("Successfully generated feed.xml")
