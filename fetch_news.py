import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from copy import deepcopy

# --- CONFIGURATION ---
DATA_EXPORT_FILE = "news_data.json"
SMALL_TOWNS = ["Clay City", "Xenia", "Sailor Springs"]
TOWNS = ["Flora", "Louisville"] + SMALL_TOWNS
RSS_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

# --- COLOR THEMES ---
THEMES = {
    "Clay City": {"bg": "#ADD8E6", "text": "#000000"},      
    "Sailor Springs": {"bg": "#367C2B", "text": "#FFDE00"}, 
    "Xenia": {"bg": "#0077BE", "text": "#FFC0CB"},          
    "Flora": {"bg": "#FFFFFF", "text": "#000000"},          
    "Louisville": {"bg": "#FFFFFF", "text": "#000000"},     
    "General": {"bg": "#808080", "text": "#FFFFFF"}         # Grey for General News
}

def clean_text(text):
    if not text: return ""
    patterns = [r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', r'(?i)by\s+tom\s+lavine']
    for p in patterns:
        text = re.sub(p, '', text)
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def get_primary_town(text):
    """Identifies if a specific town is mentioned in the story content."""
    if not text: return "General"
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
    return "General"

async def fetch_rss():
    stories = []
    namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:30]:
                    title = item.find("title").text
                    brief = item.find("description").text or ""
                    content_node = item.find("content:encoded", namespaces)
                    full_text = content_node.text if content_node is not None else brief

                    # Logic: Identify town based on Full Story content
                    town_tag = get_primary_town(full_text)
                    
                    stories.append({
                        "title": clean_text(title),
                        "brief": clean_text(brief)[:180] + "...",
                        "full_story": clean_text(full_text),
                        "link": NEWS_CENTER_URL,
                        "town_tag": town_tag,
                        "theme": THEMES.get(town_tag, THEMES["General"])
                    })
        except Exception as e:
            print(f"RSS Error: {e}")
    return stories

async def run():
    print("Gathering news and filtering duplicates...")
    all_stories = await fetch_rss()
    
    final_output = []
    seen_content = set()

    for story in all_stories:
        content_hash = story['title'] + story['town_tag']
        
        # 1. If it's a specific town mention (Clay City, Xenia, etc. in the text)
        # Keep it exactly as is.
        if story['town_tag'] in TOWNS and story['town_tag'] != "General":
            if content_hash not in seen_content:
                final_output.append(story)
                seen_content.add(content_hash)
        
        # 2. If it's a general story (like 'The ReVue') that doesn't mention a town
        # Label it General News and only keep ONE copy (deduplicate)
        else:
            story['town_tag'] = "General News"
            story['theme'] = THEMES["General"]
            if story['title'] not in seen_content:
                final_output.append(story)
                seen_content.add(story['title'])

    # Save to JSON
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(final_output, f, indent=4)

    print(f"Done! {len(final_output)} unique entries saved.")

if __name__ == "__main__":
    asyncio.run(run())
