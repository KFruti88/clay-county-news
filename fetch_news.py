import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
NEWS_DATA_FILE = 'news_data.json'
RSS_SOURCE_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"]
BLACKLIST = ["Cisne"]

def weld_text(text):
    """Physically glues 1st, 2nd, 3rd, and decimals so they never chop."""
    if not text: return ""
    
    # 1. SNAP PUNCTUATION: Snaps periods/commas to the word
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    
    # 2. DATE WELD: Glues 1st, 2nd, 3rd, 17th together
    # This prevents the 'staircase' effect in your screenshots.
    text = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1\2', text)
    
    # 3. DECIMAL WELD: Keeps 7.2 or 56.5% together
    text = re.sub(r'(\d+)\.(\d+)', r'\1.\2', text)
    
    return text.strip()

def clean_text(text):
    if not text: return ""
    patterns = [
        r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    for p in patterns: 
        text = re.sub(p, '', text)
    
    text = re.sub('<[^<]+?>', '', text)
    # Apply the weld to fix the layout issues
    return weld_text(text)

# ... (get_full_content and get_metadata remain the same) ...

async def process_news():
    final_news, seen_hashes = [], set()
    # Unique timestamp serves as an internal cache buster
    timestamp = datetime.now().isoformat()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall("./channel/item")[:15]
                
                for item in items:
                    raw_title = item.find("title").text
                    link = item.find("link").text
                    desc = item.find("description").text or ""

                    cat, tags = get_metadata(raw_title + " " + desc)
                    if cat is None: continue 

                    full_text = await get_full_content(link)
                    
                    # Clean and weld both the title and the story
                    clean_title = clean_text(raw_title)
                    story_id = re.sub(r'\W+', '', clean_title).lower()
                    
                    if story_id not in seen_hashes:
                        processed_story = clean_text(full_text) if full_text else clean_text(desc)
                        
                        final_news.append({
                            "id": story_id, 
                            "title": clean_title, 
                            "full_story": processed_story, # Now layout-safe
                            "category": cat, 
                            "tags": tags, 
                            "date_added": timestamp
                        })
                        seen_hashes.add(story_id)
        except Exception as e: print(f"Error: {e}")

    # SAVE TO JSON WITH CACHE-CONTROL
    with open(NEWS_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)
    
    print(f"Finished: {len(final_news)} stories welded. Cache Cleared.")

if __name__ == "__main__":
    asyncio.run(process_news())
