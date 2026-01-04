import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime

# --- CONFIGURATION ---
# This ensures your GitHub Action saves the file where Divi can find it
DATA_EXPORT_FILE = "calendar_events.json" 
RSS_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

# --- COLOR THEMES ---
THEMES = {
    "Clay City": {"bg": "#ADD8E6", "text": "#000000"},
    "Sailor Springs": {"bg": "#367C2B", "text": "#FFDE00"},
    "Xenia": {"bg": "#0077BE", "text": "#FFC0CB"},
    "Flora": {"bg": "#FFFFFF", "text": "#000000"},
    "Louisville": {"bg": "#FFFFFF", "text": "#000000"},
    "General News": {"bg": "#808080", "text": "#FFFFFF"}
}

def clean_text(text):
    """Scrub branding, frequencies, and leading dates for a clean Divi display."""
    if not text: return ""
    patterns = [
        r'(?i)wnoi',
        r'(?i)103\.9/99\.3',
        r'(?i)local\s*--',
        r'(?i)by\s+tom\s+lavine',
        r'^\d{1,2}/\d{1,2}/\d{2,4}\s*' # Strips date at start (e.g., 1/2/26)
    ]
    for p in patterns:
        text = re.sub(p, '', text)
    text = re.sub('<[^<]+?>', '', text) # Final HTML strip
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

async def fetch_rss():
    """Fetches and deduplicates RSS items."""
    stories = []
    seen_content = set()
    namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                today_iso = datetime.now().strftime('%Y-%m-%d')

                for item in root.findall("./channel/item")[:40]:
                    raw_title = item.find("title").text
                    brief = item.find("description").text or ""
                    content_node = item.find("content:encoded", namespaces)
                    full_text = content_node.text if content_node is not None else brief
                    
                    town_tag = get_primary_town(full_text)
                    clean_title = clean_text(raw_title)
                    
                    # DEDUPLICATION LOGIC
                    content_hash = clean_title + town_tag
                    
                    # Process: If town is mentioned, keep it. If not, consolidate to General.
                    is_general = (town_tag == "General News")
                    unique_key = clean_title if is_general else content_hash

                    if unique_key not in seen_content:
                        stories.append({
                            "title": clean_title,
                            "start": today_iso,
                            "description": clean_text(full_text),
                            "url": NEWS_CENTER_URL,
                            "backgroundColor": THEMES[town_tag]["bg"],
                            "textColor": THEMES[town_tag]["text"],
                            "extendedProps": {"town": town_tag}
                        })
                        seen_content.add(unique_key)
                            
        except Exception as e:
            print(f"RSS Error: {e}")
    return stories

async def main():
    print("Running generated RSS logic...")
    calendar_events = await fetch_rss()
    
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(calendar_events, f, indent=4)
    
    print(f"Successfully exported {len(calendar_events)} unique events to {DATA_EXPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
