import json
from datetime import datetime

# Load your JSON data
with open('news_data.json', 'r') as f:
    data = json.load(f)

rss_items = ""

# Loop through your JSON entries (assuming it's a list)
for item in data:
    rss_items += f"""
        <item>
            <title>{item.get('title', 'No Title')}</title>
            <link>{item.get('link', '')}</link>
            <description>{item.get('description', '')}</description>
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
