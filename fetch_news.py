import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DATA_EXPORT_FILE = "news_data.json"
TOWNS = ["Flora", "Clay City", "Xenia", "Louisville", "Sailor Springs"]
RSS_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

def clean_text(text):
    """Scrub branding, frequencies, reporter names, and HTML tags."""
    if not text: return ""
    patterns = [
        r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    for p in patterns:
        text = re.sub(p, '', text)
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def get_primary_town(text):
    """
    Identifies the primary town. To prevent a story from appearing on 5 pages,
    it returns only the FIRST town found.
    """
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
    """Fetches regional news and assigns a single specific town tag."""
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
                    content_tag = item.find("content:encoded", namespaces)
                    full_text = content_tag.text if content_tag is not None else brief

                    town_tag = get_primary_town(title + " " + full_text)
                    
                    stories.append({
                        "title": clean_text(title),
                        "brief": clean_text(brief)[:180] + "...",
                        "full_story": clean_text(full_text),
                        "link": NEWS_CENTER_URL,
                        "town_tag": town_tag
                    })
        except Exception as e:
            print(f"RSS Error: {e}")
    return stories

async def scrape_town(town):
    """Hits NewsBreak for town-specific updates."""
    stories = []
    url = f"https://www.newsbreak.com/search?q={town}+IL+news"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for art in soup.find_all('article')[:3]:
                    title_node = art.find('h3') or art.find('a')
                    if title_node:
                        stories.append({
                            "title": clean_text(title_node.get_text()),
                            "brief": f"Community update for {town}.",
                            "full_story": f"Detailed community updates for {town}. Visit the News Center for the full report.",
                            "link": NEWS_CENTER_URL,
                            "town_tag": town
                        })
        except Exception as e:
            print(f"Scrape Error for {town}: {e}")
    return stories

async def run():
    seen_stories = {} 

    print("Gathering news...")
    
    # 1. Process RSS
    regional = await fetch_rss()
    for story in regional:
        seen_stories[story['title']] = story

    # 2. Process Town Scrapes
    for town in TOWNS:
        print(f"Checking {town}...")
        town_stories = await scrape_town(town)
        for story in town_stories:
            title = story['title']
            if title not in seen_stories:
                seen_stories[title] = story

    # 3. Export to JSON
    final_list = list(seen_stories.values())
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(final_list, f, indent=4)
        
    print(f"Update complete! Saved {len(final_list)} unique stories to {DATA_EXPORT_FILE}")

if __name__ == "__main__":
    # Corrected the 'async asyncio.run' typo
    asyncio.run(run())
