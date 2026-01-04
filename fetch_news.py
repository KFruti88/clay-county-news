import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import os

# --- CONFIGURATION ---
FEED_XML_FILE = 'feed.xml'              # Output for RSS readers
CALENDAR_JSON_FILE = "calendar_events.json"  # Output for Divi/FullCalendar
RSS_SOURCE_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

# --- COLOR THEMES ---
# These are mapped to specific towns or the general fallback
THEMES = {
    "Clay City": {"bg": "#ADD8E6", "text": "#000000"},
    "Sailor Springs": {"bg": "#367C2B", "text": "#FFDE00"},
    "Xenia": {"bg": "#0077BE", "text": "#FFC0CB"},
    "Flora": {"bg": "#FFFFFF", "text": "#000000"},
    "Louisville": {"bg": "#FFFFFF", "text": "#000000"},
    "General News": {"bg": "#808080", "text": "#FFFFFF"}
}

def clean_text(text):
    """Scrub branding, frequencies, and leading dates for a clean display."""
    if not text: return ""
    
    # Combined and cleaned patterns from your logic
    patterns = [
        r'(?i)wnoi', 
        r'(?i)103\.9/99\.3', 
        r'(?i)local\s*--',
        r'(?i)by\s+tom\s+lavine', 
        r'^\d{1,2}/\d{1,2}/\d{2,4}\s*' # Strips date at the very start of strings
    ]
    
    for p in patterns:
        text = re.sub(p, '', text)
        
    # Remove HTML tags and extra whitespace
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def get_primary_town(text):
    """Checks the full story content for specific town mentions."""
    if not text: return "General News"
    
    town_map = {
        "Flora": r'(?i)\bflora\b',
        "Xenia": r'(?i)\bxenia\b',
        "Louisville": r'(?i)\blouisville\b',
        "Clay City": r'(?i)clay\s*city',
        "Sailor Springs": r'(?i)sailor\s*springs'
    }
    
    for town, pattern in town_map.items():
        if re.search(pattern, text):
            return town
            
    return "General News"

async def process_news():
    """Main logic: Fetches external RSS, cleans it, and generates XML/JSON outputs."""
    stories = []
    seen_content = set()
    namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
    
    # 
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                today_iso = datetime.now().strftime('%Y-%m-%d')
                pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

                rss_items_xml = ""

                # Process the top 40 items from the feed
                for item in root.findall("./channel/item")[:40]:
                    raw_title = item.find("title").text
                    brief = item.find("description").text or ""
                    content_node = item.find("content:encoded", namespaces)
                    full_text = content_node.text if content_node is not None else brief
                    
                    town_tag = get_primary_town(full_text)
                    clean_title = clean_text(raw_title)
                    
                    # Deduplication Logic
                    # If it's general news, we only want one copy of that headline.
                    # If it's town news, we allow it if the town+headline combo is unique.
                    is_general = (town_tag == "General News")
                    unique_key = clean_title if is_general else (clean_title + town_tag)

                    if unique_key not in seen_content:
                        # 1. Prepare data for JSON (FullCalendar format)
                        stories.append({
                            "title": clean_title,
                            "start": today_iso,
                            "description": clean_text(full_text),
                            "url": NEWS_CENTER_URL,
                            "backgroundColor": THEMES[town_tag]["bg"],
                            "textColor": THEMES[town_tag]["text"],
                            "extendedProps": {"town": town_tag}
                        })
                        
                        # 2. Prepare data for XML (Standard RSS format)
                        rss_items_xml += f"""
        <item>
            <title>{clean_title}</title>
            <link>{NEWS_CENTER_URL}</link>
            <description>{clean_text(brief[:200])}...</description>
            <pubDate>{pub_date}</pubDate>
        </item>"""
                        
                        seen_content.add(unique_key)

                # Save Calendar JSON
                with open(CALENDAR_JSON_FILE, "w") as f:
                    json.dump(stories, f, indent=4)
                print(f"Exported {len(stories)} unique events to {CALENDAR_JSON_FILE}")

                # Save RSS XML
                rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
    <channel>
        <title>Clay County News Feed</title>
        <link>{NEWS_CENTER_URL}</link>
        <description>Cleaned and Categorized Clay County News</description>
        {rss_items_xml}
    </channel>
</rss>"""
                with open(FEED_XML_FILE, 'w') as f:
                    f.write(rss_feed)
                print(f"Successfully generated {FEED_XML_FILE}")

        except Exception as e:
            print(f"Error during processing: {e}")

if __name__ == "__main__":
    asyncio.run(process_news())
