import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
NEWS_DATA_FILE = 'news_data.json'
RSS_SOURCE_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

def clean_text(text):
    if not text: return ""
    patterns = [r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*']
    for p in patterns:
        text = re.sub(p, '', text)
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def get_metadata(text):
    """Detects Category, Emojis, and ALL mentioned towns."""
    # 1. Category Detection
    category = "General News"
    icon = ""
    if re.search(r'(?i)\bobituary\b|\bobituaries\b|\bpassed\s*away\b', text):
        category = "Obituary"; icon = "🕊️ "
    elif re.search(r'(?i)\bfire\b|\brescue\b|\bextrication\b|\bstructure\s*fire\b', text):
        category = "Fire & Rescue"; icon = "🚒 "
    elif re.search(r'(?i)\barrest\b|\bsheriff\b|\bpolice\b|\bbooking\b|\bblotter\b', text):
        category = "Police Report"; icon = "🚨 "

    # 2. Multi-Town Tagging
    town_tags = []
    town_map = {
        "Flora": r'(?i)\bflora\b',
        "Xenia": r'(?i)\bxenia\b',
        "Louisville": r'(?i)\blouisville\b',
        "Clay City": r'(?i)clay\s*city',
        "Sailor Springs": r'(?i)sailor\s*springs'
    }
    
    for town, pattern in town_map.items():
        if re.search(pattern, text):
            town_tags.append(town)
    
    # If no specific town is found, or as a global fallback
    if not town_tags:
        town_tags.append("County News")
    
    return category, town_tags, icon

async def process_news():
    final_news = []
    seen_hashes = set() # Global deduplication
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    timestamp = datetime.now().isoformat()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
                for item in root.findall("./channel/item")[:40]:
                    raw_title = item.find("title").text
                    full_text = (item.find("content:encoded", namespaces).text 
                                 if item.find("content:encoded", namespaces) is not None 
                                 else item.find("description").text)
                    
                    category, tags, icon = get_metadata(raw_title + " " + full_text)
                    clean_title = f"{icon}{clean_text(raw_title)}"
                    
                    # Deduplication check
                    content_hash = re.sub(r'\W+', '', clean_title).lower()
                    if content_hash not in seen_hashes:
                        final_news.append({
                            "title": clean_title,
                            "description": clean_text(full_text),
                            "category": category,
                            "tags": tags, # List of towns: e.g. ["Flora", "County News"]
                            "link": NEWS_CENTER_URL,
                            "date_added": timestamp
                        })
                        seen_hashes.add(content_hash)
        except Exception as e:
            print(f"Error: {e}")

    # Save as JSON
    with open(NEWS_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)

    print(f"Update complete. {len(final_news)} unique items stored.")

if __name__ == "__main__":
    asyncio.run(process_news())
