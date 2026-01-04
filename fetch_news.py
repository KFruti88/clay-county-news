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
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"]
BLACKLIST = ["Cisne"]

def weld_text(text):
    """Physically glues 1st, 2nd, 3rd, and decimals so they never chop."""
    if not text: return ""
    
    # 1. SNAP PUNCTUATION: Snaps periods/commas to the word
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    
    # 2. DATE WELD: Glues 1st, 2nd, 3rd, 17th together
    text = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1\2', text)
    
    # 3. DECIMAL WELD: Keeps 7.2 or 56.5% together
    text = re.sub(r'(\d+)\.(\d+)', r'\1.\2', text)
    
    return text.strip()

def clean_text(text):
    """
    Cleans unwanted radio station signatures but keeps emails intact.
    """
    if not text: return ""
    
    # Remove HTML tags but leave the inner text (important for keeping email text)
    text = re.sub(r'<[^>]+>', ' ', text)

    patterns = [
        r'(?i)wnoi', 
        r'(?i)103\.9/99\.3', 
        r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', 
        r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    for p in patterns: 
        text = re.sub(p, '', text)
    
    # Apply the weld to fix layout issues while keeping prose readable
    return weld_text(text)

async def get_full_content(url):
    """Fetches the full article text from the website."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                content = soup.find('div', class_='entry-content')
                # get_text(separator=' ') preserves spacing around links/emails
                return content.get_text(separator=' ') if content else ""
    except:
        return ""
    return ""

def get_metadata(text):
    """
    Dynamic Town Tagging:
    - If ONE town found: Tag that town.
    - If MULTIPLE towns found: Tag 'County News'.
    - If NO towns found: Tag 'County News'.
    """
    text_lower = text.lower()
    
    if any(bad.lower() in text_lower for bad in BLACKLIST):
        return None, []

    found_towns = [town for town in TOWNS if town.lower() in text_lower]

    if len(found_towns) == 1:
        category = "General News"
        tags = [found_towns[0]]
    else:
        # This covers 0 towns OR 2+ towns
        category = "General News"
        tags = ["County News"]

    return category, tags

async def process_news():
    final_news, seen_hashes = [], set()
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

                    # 1. Fetch full content first
                    full_text = await get_full_content(link)
                    combined_text = raw_title + " " + (full_text if full_text else desc)

                    # 2. Town Logic
                    cat, tags = get_metadata(combined_text)
                    if cat is None: continue 

                    # 3. Processing
                    clean_title = clean_text(raw_title)
                    story_id = re.sub(r'\W+', '', clean_title).lower()
                    
                    if story_id not in seen_hashes:
                        # Use full_text if available, otherwise desc
                        raw_story = full_text if full_text else desc
                        processed_story = clean_text(raw_story)
                        
                        final_news.append({
                            "id": story_id, 
                            "title": clean_title, 
                            "full_story": processed_story,
                            "category": cat, 
                            "tags": tags, 
                            "date_added": timestamp
                        })
                        seen_hashes.add(story_id)
        except Exception as e: 
            print(f"Error: {e}")

    # SAVE TO JSON
    with open(NEWS_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)
    
    print(f"Finished: {len(final_news)} stories. Emails preserved, Towns categorized.")

if __name__ == "__main__":
    asyncio.run(process_news())
