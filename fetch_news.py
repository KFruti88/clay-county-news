import asyncio
import json
import os
import re
import httpx
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DATA_EXPORT_FILE = "news_data.json"
TOWNS = ["Flora", "Clay City", "Xenia", "Louisville", "Sailor Springs"]
RSS_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

def clean_text(text):
    if not text: return ""
    patterns = [
        r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    for p in patterns:
        text = re.sub(p, '', text)
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def contains_clay_county_keywords(text):
    if not text: return False
    keywords = [r'(?i)flora', r'(?i)xenia', r'(?i)louisville', r'(?i)clay\s*city', r'(?i)sailor\s*springs', r'(?i)clay\s*county']
    return any(re.search(k, text) for k in keywords)

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
                    brief = item.find("description").text or ""
                    content_tag = item.find("content:encoded", namespaces)
                    full_story_raw = content_tag.text if content_tag is not None else brief

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

# --- THE FIX IS IN THIS FUNCTION ---
async def run():
    all_unique_stories = []
    seen_titles = set() # This "memory" prevents duplicates

    print("Scanning regional feeds...")
    regional = await fetch_rss()
    
    # Add regional stories first, marking them as 'seen'
    for story in regional:
        if story['title'] not in seen_titles:
            all_unique_stories.append(story)
            seen_titles.add(story['title'])

    for town in TOWNS:
        print(f"Processing {town}...")
        town_specific = await scrape_town(town)
        for story in town_specific:
            if story['title'] not in seen_titles:
                all_unique_stories.append(story)
                seen_titles.add(story['title'])
        
    # Save as a single list instead of a dictionary grouped by town
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(all_unique_stories, f, indent=4)
        
    print(f"Update complete! Saved {len(all_unique_stories)} unique stories to {DATA_EXPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(run())
