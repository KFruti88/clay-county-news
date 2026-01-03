import httpx
import asyncio
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

# Configuration
DATA_EXPORT_FILE = "news_data.json"
HISTORY_FILE = "posted_links.json"
TOWNS = ["Flora", "Clay City", "Xenia", "Louisville", "Sailor Springs"]
RSS_FEED_URL = "https://www.wnoi.com/category/local/feed"

def clean_text(text):
    """Removes source branding and extra noise from headlines and briefs."""
    if not text: return ""
    # Patterns to remove: WNOI, NewsBreak, Radio, Reporters, etc.
    remove_patterns = [
        r'(?i)wnoi', r'(?i)newsbreak', r'(?i)radio', r'(?i)local\s*news:',
        r'(?i)by\s+[a-z\s]+', r'(?i)effingham\s*daily\s*news', r'(?i)st\.\s*louis'
    ]
    for pattern in remove_patterns:
        text = re.sub(pattern, '', text)
    # Clean up HTML tags and leading/trailing punctuation
    text = re.sub('<[^<]+?>', '', text)
    text = re.sub(r'^\s*[:\-\|]\s*', '', text)
    return text.strip()

async def fetch_rss_news():
    """Fetches regional news from WNOI RSS and cleans it."""
    stories = []
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(RSS_FEED_URL, timeout=15)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall("./channel/item")
                for item in items[:8]: # Get top 8 regional stories
                    title = item.find("title").text
                    brief = item.find("description").text or ""
                    stories.append({
                        "title": clean_text(title),
                        "brief": clean_text(brief)[:160] + "...",
                        "link": "https://supportmylocalcommunity.com/clay-county-news-center/"
                    })
        except Exception as e:
            print(f"RSS Error: {e}")
    return stories

async def scrape_newsbreak(town):
    """Your existing NewsBreak scraper logic goes here."""
    # ... (Keep your existing scraping code but use clean_text() on results)
    return [] 

async def run_pipeline():
    all_results = {}
    
    # 1. Fetch Regional RSS News once
    regional_news = await fetch_rss_news()
    
    # 2. Process each town
    for town in TOWNS:
        # Get town-specific news from scraper
        town_stories = await scrape_newsbreak(town)
        
        # Combine with regional RSS stories
        # This ensures every town page has regional updates
        all_results[town] = town_stories + regional_news

    # 3. Save to JSON for WordPress to read
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(all_results, f, indent=4)
    print(f"Pipeline complete. Data saved to {DATA_EXPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
