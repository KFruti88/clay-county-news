import httpx
import asyncio
import json
import os
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DATA_EXPORT_FILE = "news_data.json"
TOWNS = ["Flora", "Clay City", "Xenia", "Louisville", "Sailor Springs"]
RSS_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

def clean_text(text):
    """Removes branding, frequencies, and reporter names."""
    if not text: return ""
    patterns = [
        r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    for p in patterns:
        text = re.sub(p, '', text)
    # Remove HTML tags to keep the JSON clean
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

async def fetch_rss():
    """Fetches news and extracts FULL content using namespaces."""
    stories = []
    # This namespace is the 'key' to unlocking the full story tag
    namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:10]:
                    title = item.find("title").text
                    # 'description' is the short teaser
                    brief = item.find("description").text or ""
                    
                    # 'content:encoded' is the full article text
                    content_tag = item.find("content:encoded", namespaces)
                    full_story_raw = content_tag.text if content_tag is not None else brief
                    
                    stories.append({
                        "title": clean_text(title),
                        "brief": clean_text(brief)[:180] + "...",
                        "full_story": clean_text(full_story_raw), 
                        "link": NEWS_CENTER_URL
                    })
        except Exception as e:
            print(f"RSS Error: {e}")
    return stories

async def scrape_town(town):
    """Scrapes NewsBreak for town-specific headlines."""
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
                            "full_story": f"Check our News Center for full details on {town} community updates.",
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
        # Combine town news with regional news
        all_news[town] = town_specific + regional
        
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(all_news, f, indent=4)
    print(f"Successfully updated {DATA_EXPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(run())
