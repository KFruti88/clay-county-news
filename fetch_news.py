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
    """
    Removes branding (WNOI, NewsBreak), 'By' lines, and HTML tags.
    Ensures no 'Thank you' or 'Subscribe' text is added.
    """
    if not text: return ""
    
    # List of branding keywords to scrub
    remove_patterns = [
        r'(?i)wnoi', r'(?i)newsbreak', r'(?i)radio', r'(?i)local\s*news:',
        r'(?i)by\s+[a-z\s]+', r'(?i)effingham\s*daily\s*news', r'(?i)st\.\s*louis',
        r'(?i)olney', r'(?i)salem', r'(?i)fairfield', r'(?i)mt\.\s*vernon'
    ]
    for pattern in remove_patterns:
        text = re.sub(pattern, '', text)
    
    # Remove HTML tags and clean up leading/trailing symbols
    text = re.sub('<[^<]+?>', '', text)
    text = re.sub(r'^\s*[:\-\|]\s*', '', text)
    return text.strip()

async def fetch_rss():
    """Regional news from WNOI RSS."""
    stories = []
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                # Get latest 8 stories from the feed
                for item in root.findall("./channel/item")[:8]:
                    title = item.find("title").text
                    brief = item.find("description").text or ""
                    stories.append({
                        "title": clean_text(title),
                        "brief": clean_text(brief)[:180] + "...",
                        "link": NEWS_CENTER_URL
                    })
        except Exception as e:
            print(f"RSS Error: {e}")
    return stories

async def scrape_town(town):
    """Town-specific news from NewsBreak."""
    stories = []
    url = f"https://www.newsbreak.com/search?q={town}+IL+news"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            # Use standard browser header to avoid being blocked
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Limit to top 3 articles per town
                for art in soup.find_all('article')[:3]:
                    title_node = art.find('h3') or art.find('a')
                    if title_node:
                        stories.append({
                            "title": clean_text(title_node.get_text()),
                            "brief": f"Community update for {town}.",
                            "link": NEWS_CENTER_URL
                        })
        except Exception as e:
            print(f"Scrape Error for {town}: {e}")
    return stories

async def run():
    all_news = {}
    print("Fetching regional RSS news...")
    regional = await fetch_rss()
    
    for town in TOWNS:
        print(f"Aggregating news for {town}...")
        town_specific = await scrape_town(town)
        # Merge town-specific scrapes with regional RSS news
        all_news[town] = town_specific + regional
        
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(all_news, f, indent=4)
    print(f"Success: {DATA_EXPORT_FILE} updated without metadata or branding.")

if __name__ == "__main__":
    asyncio.run(run())
