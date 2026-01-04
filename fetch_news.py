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

async def get_full_content(url):
    """Visits the actual website to grab the full article text."""
    try:
        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}, timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # WNOI usually puts the full story in 'entry-content'
                article = soup.find('div', class_='entry-content')
                if article:
                    # Remove social media buttons and ads
                    for junk in article.find_all(['script', 'style', 'div'], class_=['sharedaddy', 'jp-relatedposts']):
                        junk.decompose()
                    return article.get_text(separator="\n").strip()
    except: pass
    return None

def get_metadata(text):
    text_lower = text.lower()
    # Check Blacklist
    if any(forbidden.lower() in text_lower for forbidden in BLACKLIST):
        return None, None

    cat = "General News"
    if any(word in text_lower for word in ['musical', 'music', 'concert', 'revue']):
        cat = "Arts & Entertainment"
    elif any(word in text_lower for word in ['obituary', 'passed away']):
        cat = "Obituary"
    elif any(word in text_lower for word in ['arrest', 'sheriff', 'police', 'jail']):
        cat = "Police Report"
    elif any(word in text_lower for word in ['school', 'student', 'gingerbread']):
        cat = "School News"
    elif any(word in text_lower for word in ['tax', 'pritzker', 'governor']):
        cat = "State News"

    found_towns = [t for t in TOWNS if re.search(fr'(?i)\b{t}\b', text)]
    
    # Tagging Logic
    if len(found_towns) > 1 or cat == "State News" or len(found_towns) == 0:
        town_tags = ["County News"]
    else:
        town_tags = found_towns
    
    return cat, town_tags

async def process_news():
    final_news, seen_hashes = [], set()
    timestamp = datetime.now().isoformat()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall("./channel/item")[:15] # Top 15 stories
                
                for item in items:
                    raw_title = item.find("title").text
                    link = item.find("link").text
                    desc = item.find("description").text or ""

                    cat, tags = get_metadata(raw_title + " " + desc)
                    if cat is None: continue 

                    # DEEP SCRAPE: Get the actual long story text
                    full_text = await get_full_content(link)
                    
                    clean_title = clean_text(raw_title)
                    story_id = re.sub(r'\W+', '', clean_title).lower()
                    
                    if story_id not in seen_hashes:
                        final_news.append({
                            "id": story_id, 
                            "title": clean_title, 
                            "summary": clean_text(desc).replace('[&#8230;]', '...'),
                            "full_story": full_text if full_text else clean_text(desc),
                            "category": cat, 
                            "tags": tags, 
                            "link": f"{NEWS_CENTER_URL}#{story_id}", 
                            "date_added": timestamp
                        })
                        seen_hashes.add(story_id)
        except Exception as e: print(f"Error: {e}")

    # SAVE TO JSON
    with open(NEWS_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)
    print(f"Finished: {len(final_news)} stories saved.")

if __name__ == "__main__":
    asyncio.run(process_news())
