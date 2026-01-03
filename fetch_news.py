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
    """Scrub branding, frequencies, reporter names, and HTML."""
    if not text: return ""
    patterns = [
        r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    for p in patterns:
        text = re.sub(p, '', text)
    # Remove HTML tags
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def contains_clay_county_keywords(text):
    """
    The 'Smart Scanner': Returns True if a Clay County town is mentioned.
    This allows news from nearby cities to pass IF they mention your towns.
    """
    if not text: return False
    keywords = [
        r'(?i)flora', r'(?i)xenia', r'(?i)louisville', 
        r'(?i)clay\s*city', r'(?i)sailor\s*springs', r'(?i)clay\s*county'
    ]
    return any(re.search(k, text) for k in keywords)

async def fetch_rss():
    """Fetches regional news and filters for relevance to your towns."""
    stories = []
    # Key to unlocking the full story tag
    namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                # Scan top 30 to find hidden mentions of your specific towns
                for item in root.findall("./channel/item")[:30]:
                    title = item.find("title").text
                    brief = item.find("description").text or ""
                    
                    # Grab the FULL article text
                    content_tag = item.find("content:encoded", namespaces)
                    full_story_raw = content_tag.text if content_tag is not None else brief
                    
                    # SCANNER LOGIC: Only keep if your towns are mentioned anywhere
                    if (contains_clay_county_keywords(title) or 
                        contains_clay_county_keywords(brief) or 
                        contains_clay_county_keywords(full_story_raw)):
                        
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
    """Hits NewsBreak specifically for each town's search page."""
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
                            "full_story": f"Detailed update for {town}.",
                            "link": NEWS_CENTER_URL
                        })
        except Exception as e:
            print(f"Scrape Error for {town}: {e}")
    return stories

async def run():
    all_news = {}
    print("Scanning regional feeds for Clay County mentions...")
    regional = await fetch_rss()
    for town in TOWNS:
        print(f"Processing {town}...")
        town_specific = await scrape_town(town)
        all_news[town] = town_specific + regional
        
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(all_news, f, indent=4)
    print(f"Update complete: {DATA_EXPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(run())
