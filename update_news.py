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
    """Prevents layout breaking by 'gluing' dates, decimals, and punctuation."""
    if not text: return ""
    # Snaps punctuation to the word
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    # Glues 1st, 2nd, etc.
    text = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1\2', text)
    # Glues decimals like 56.5%
    text = re.sub(r'(\d+)\.(\d+)', r'\1.\2', text)
    return text.strip()

def clean_text(text):
    """Cleans station signatures but strictly preserves email addresses."""
    if not text: return ""
    # Strip HTML tags but preserve inner text (crucial for emails)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    patterns = [
        r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    for p in patterns: 
        text = re.sub(p, '', text)
    
    return weld_text(text)

async def get_full_content(url):
    """Fetches full story text from WNOI."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                content = soup.find('div', class_='entry-content')
                # separator=' ' ensures email/link text doesn't mash into nearby words
                return content.get_text(separator=' ') if content else ""
    except:
        return ""
    return ""

def get_metadata(text):
    """
    Identifies ALL mentioned towns for multi-page visibility.
    If no towns match, it defaults to 'County News'.
    """
    text_lower = text.lower()
    if any(bad.lower() in text_lower for bad in BLACKLIST):
        return None, []

    # Creates a list of all towns found in the story
    found_towns = [town for town in TOWNS if town.lower() in text_lower]
    
    # Logic: Use found towns as tags, or fallback to County News
    assigned_tags = found_towns if found_towns else ["County News"]
    
    return "General News", assigned_tags

async def process_news():
    final_news = []
    seen_ids = set() # THE DEDUPLICATOR: Prevents duplicate stories in JSON
    timestamp = datetime.now().isoformat()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall("./channel/item")[:20]
                
                for item in items:
                    raw_title = item.find("title").text
                    link = item.find("link").text
                    desc = item.find("description").text or ""

                    # --- DEDUPLICATION CHECK ---
                    story_id = re.sub(r'\W+', '', raw_title).lower()
                    if story_id in seen_ids:
                        continue # Skip this loop; we already have this story
                    seen_ids.add(story_id)

                    full_text = await get_full_content(link)
                    check_text = raw_title + " " + (full_text if full_text else desc)
                    
                    cat, tags = get_metadata(check_text)
                    if cat is None: continue 

                    clean_title = clean_text(raw_title)
                    story_body = full_text if full_text else desc
                    
                    final_news.append({
                        "id": story_id, 
                        "title": clean_title, 
                        "full_story": clean_text(story_body), 
                        "category": cat, 
                        "tags": tags,
                        "link": link,
                        "date_added": timestamp
                    })
        except Exception as e: 
            print(f"Error: {e}")

    # Final Save
    with open(NEWS_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)
    
    print(f"Update complete. {len(final_news)} unique stories processed.")

if __name__ == "__main__":
    asyncio.run(process_news())
