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
NEWS_CENTER = "https://supportmylocalcommunity.com/clay-county-news-center/"

def clean_text(text):
    """Scrub branding and source tags."""
    if not text: return ""
    patterns = [r'(?i)wnoi', r'(?i)newsbreak', r'(?i)radio', r'(?i)local\s*news:']
    for p in patterns:
        text = re.sub(p, '', text)
    return re.sub('<[^<]+?>', '', text).strip()

async def fetch_rss():
    """Regional news from WNOI."""
    stories = []
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:8]:
                    stories.append({
                        "title": clean_text(item.find("title").text),
                        "brief": clean_text(item.find("description").text)[:180] + "...",
                        "link": NEWS_CENTER
                    })
        except Exception as e: print(f"RSS Error: {e}")
    return stories

async def scrape_town(town):
    """Town-specific news from NewsBreak."""
    stories = []
    url = f"https://www.newsbreak.com/search?q={town}+IL+news"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for art in soup.find_all('article')[:3]:
                    title = art.find('h3') or art.find('a')
                    if title:
                        stories.append({
                            "title": clean_text(title.get_text()),
                            "brief": f"Community update for {town}.",
                            "link": NEWS_CENTER
                        })
        except Exception as e: print(f"Scrape Error: {e}")
    return stories

async def run():
    all_news = {}
    regional = await fetch_rss()
    for town in TOWNS:
        all_news[town] = (await scrape_town(town)) + regional
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(all_news, f, indent=4)

if __name__ == "__main__":
    asyncio.run(run())
