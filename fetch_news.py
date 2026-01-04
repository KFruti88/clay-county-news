import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DATA_EXPORT_FILE = "news_data.json"
SMALL_TOWNS = ["Clay City", "Xenia", "Sailor Springs"]
TOWNS = ["Flora", "Louisville"] + SMALL_TOWNS
RSS_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

# --- COLOR THEMES ---
THEMES = {
    "Clay City": {"bg": "#ADD8E6", "text": "#000000"},      # Light Blue / Black
    "Sailor Springs": {"bg": "#367C2B", "text": "#FFDE00"}, # JD Green / JD Yellow
    "Xenia": {"bg": "#0077BE", "text": "#FFC0CB"},          # Ocean Blue / Pink
    "Flora": {"bg": "#FFFFFF", "text": "#000000"},          # Default White/Black
    "Louisville": {"bg": "#FFFFFF", "text": "#000000"},     # Default White/Black
    "General": {"bg": "#F4F4F4", "text": "#333333"}         # Soft Grey for County News
}

def clean_text(text):
    if not text: return ""
    patterns = [r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', r'(?i)by\s+tom\s+lavine']
    for p in patterns:
        text = re.sub(p, '', text)
    return re.sub('<[^<]+?>', '', text).strip()

def get_primary_town(text):
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
                    full_text = (item.find("content:encoded", namespaces).text 
                                 if item.find("content:encoded", namespaces) is not None 
                                 else item.find("description").text)
                    
                    town_tag = get_primary_town(title + " " + (full_text or ""))
                    
                    stories.append({
                        "title": clean_text(title),
                        "full_story": clean_text(full_text),
                        "town_tag": town_tag,
                        "theme": THEMES.get(town_tag, THEMES["General"])
                    })
        except Exception as e: print(f"RSS Error: {e}")
    return stories

async def run():
    seen_stories = {}
    print("Gathering news and applying themes...")

    # 1. Fetch all unique stories
    all_raw_stories = await fetch_rss()
    for s in all_raw_stories:
        seen_stories[s['title']] = s

    # 2. Logic: Ensure small towns have content (Fallback to General)
    final_output = []
    unique_list = list(seen_stories.values())
    
    # We want to make sure the JSON includes entries for small towns 
    # even if they are just duplicates of "General" news with the town's colors.
    for town in TOWNS:
        town_news = [s for s in unique_list if s['town_tag'] == town]
        
        if town in SMALL_TOWNS and not town_news:
            # Grab General news but RE-COLOR it for the specific town
            general_news = [s for s in unique_list if s['town_tag'] == "General"]
            for g in general_news:
                fallback_story = g.copy()
                fallback_story['town_tag'] = town # Tag it so the page finds it
                fallback_story['theme'] = THEMES[town] # Apply town colors
                final_output.append(fallback_story)
        else:
            final_output.extend(town_news)

    # 3. Save to JSON
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(final_output, f, indent=4)

    print(f"Complete! JSON updated with {len(final_output)} entries and custom themes.")

if __name__ == "__main__":
    asyncio.run(run())
