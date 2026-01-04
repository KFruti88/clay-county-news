import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from copy import deepcopy

# --- CONFIGURATION ---
DATA_EXPORT_FILE = "news_data.json"
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"]
RSS_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

# --- COLOR THEMES ---
THEMES = {
    "Clay City": {"bg": "#ADD8E6", "text": "#000000"},      
    "Sailor Springs": {"bg": "#367C2B", "text": "#FFDE00"}, 
    "Xenia": {"bg": "#0077BE", "text": "#FFC0CB"},          
    "Flora": {"bg": "#FFFFFF", "text": "#000000"},          
    "Louisville": {"bg": "#FFFFFF", "text": "#000000"},     
    "General News": {"bg": "#808080", "text": "#FFFFFF"}    # Consolidated Grey
}

def clean_text(text):
    """Scrub branding, frequencies, dates, and HTML tags."""
    if not text: return ""
    # Your updated pattern list including date stripping
    patterns = [
        r'(?i)wnoi', 
        r'(?i)103\.9/99\.3', 
        r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', 
        r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
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

async def fetch_rss():
    """Fetches RSS feed and assigns town_tags based on STORY content."""
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

                    # Logic: Determine town tag based on the STORY content keywords
                    town_tag = get_primary_town(full_text)
                    
                    stories.append({
                        "title": clean_text(title),
                        "brief": clean_text(brief)[:180] + "...",
                        "full_story": clean_text(full_text),
                        "link": NEWS_CENTER_URL,
                        "town_tag": town_tag,
                        "theme": THEMES.get(town_tag, THEMES["General News"])
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
        # Create a unique key to identify duplicates
        content_hash = story['title'] + story['town_tag']
        
        # CATEGORY 1: Specific Town News (Town is actually mentioned in the text)
        if story['town_tag'] != "General News":
            if content_hash not in seen_content:
                final_output.append(story)
                seen_content.add(content_hash)
        
        # CATEGORY 2: General News (Consolidate repeats like 'The ReVue')
        else:
            # Only allow ONE instance of a General News story title to exist
            if story['title'] not in seen_content:
                story['town_tag'] = "General News"
                story['theme'] = THEMES["General News"]
                final_output.append(story)
                seen_content.add(story['title'])

    # Save the clean, de-duplicated list to the JSON file
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(final_output, f, indent=4)

    print(f"Done! {len(final_output)} unique entries saved to {DATA_EXPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(run())
