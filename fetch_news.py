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
    """Scrub branding, frequencies, and reporter names."""
    if not text: return ""
    patterns = [
        r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    for p in patterns:
        text = re.sub(p, '', text)
    text = re.sub('<[^<]+?>', '', text) # Remove HTML tags
    return text.strip()

async def fetch_rss():
    """Fetches news and extracts full content from 'content:encoded'."""
    stories = []
    # This namespace is critical for reading the 'content:encoded' tag
    namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:8]:
                    title = item.find("title").text
                    brief = item.find("description").text or ""
                    
                    # --- NEW: Grab the FULL STORY ---
                    full_content_node = item.find("content:encoded", namespaces)
                    full_story = full_content_node.text if full_content_node is not None else brief
                    
                    stories.append({
                        "title": clean_text(title),
                        "brief": clean_text(brief)[:180] + "...",
                        "full_story": clean_text(full_story), # The full unbranded article
                        "link": NEWS_CENTER_URL
                    })
        except Exception as e:
            print(f"RSS Error: {e}")
    return stories

async def scrape_town(town):
    """NewsBreak scraper logic (Briefs only as per site layout)."""
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
                            "full_story": f"Check our News Center for more details on {town}.",
                            "link": NEWS_CENTER_URL
                        })
        except Exception as e:
            print(f"Scrape Error for {town}: {e}")
    return stories

async def run():
    all_news = {}
    print("Gathering regional news...")
    regional = await fetch_rss()
    for town in TOWNS:
        print(f"Processing {town}...")
        town_specific = await scrape_town(town)
        all_news[town] = town_specific + regional
        
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(all_news, f, indent=4)
    print(f"Successfully updated {DATA_EXPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(run())
