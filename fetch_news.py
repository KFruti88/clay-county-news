import httpx
import asyncio
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DATA_EXPORT_FILE = "news_data.json"
HISTORY_FILE = "posted_links.json"
TOWNS = ["Flora", "Clay City", "Xenia", "Louisville", "Sailor Springs"]
RSS_FEED_URL = "https://www.wnoi.com/category/local/feed"
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

async def fetch_rss_news():
    """Fetches regional news from WNOI RSS."""
    stories = []
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(RSS_FEED_URL, timeout=15)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall("./channel/item")
                # Get top 8 regional stories
                for item in items[:8]:
                    title = item.find("title").text
                    brief = item.find("description").text or ""
                    stories.append({
                        "title": clean_text(title),
                        "brief": clean_text(brief)[:180] + "...",
                        "link": NEWS_CENTER_URL 
                    })
        except Exception as e:
            print(f"RSS Fetch Error: {e}")
    return stories

async def scrape_town_news(town):
    """Scrapes NewsBreak for town-specific headlines."""
    stories = []
    search_url = f"https://www.newsbreak.com/search?q={town}+IL+news"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = await client.get(search_url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Limit to top 3 articles per town
                articles = soup.find_all('article')[:3] 
                for art in articles:
                    title_tag = art.find('h3') or art.find('a')
                    if title_tag:
                        stories.append({
                            "title": clean_text(title_tag.get_text()),
                            "brief": f"Recent community update for {town}.",
                            "link": NEWS_CENTER_URL
                        })
        except Exception as e:
            print(f"Scrape Error for {town}: {e}")
    return stories

async def run_pipeline():
    all_results = {}

    # 1. Fetch regional stories once
    print("Fetching regional RSS news...")
    regional_news = await fetch_rss_news()

    # 2. Collect town news and merge with regional news
    for town in TOWNS:
        print(f"Aggregating news for {town}...")
        town_specific = await scrape_town_news(town)
        # Merge town-specific news with the regional RSS feed
        all_results[town] = town_specific + regional_news

    # 3. Save only clean data to JSON
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(all_results, f, indent=4)
    
    print(f"Success: {DATA_EXPORT_FILE} updated without metadata or branding.")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
