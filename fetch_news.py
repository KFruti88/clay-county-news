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
    """Removes branding, extra spaces, and HTML tags."""
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
                article = soup.find('div', class_='entry-content')
                if article:
                    # Clean out social sharing junk
                    for tag in article.find_all(['script', 'style', 'div']):
                        if tag.get('class') and any(c in tag.get('class') for c in ['sharedaddy', 'jp-relatedposts']):
                            tag.decompose()
                    return article.get_text(separator="\n").strip()
    except: pass
    return None

def get_metadata(text):
    """Categorization with strict Blacklist and smart town logic."""
    text_lower = text.lower()
    if any(forbidden.lower() in text_lower for forbidden in BLACKLIST):
        return None, None

    cat = "General News"
    # Priority Categories
    if any(word in text_lower for word in ['musical', 'music', 'concert', 'band', 'revue', 'burmashavers']):
        cat = "Arts & Entertainment"
    elif any(word in text_lower for word in ['obituary', 'obituaries', 'passed away']):
        cat = "Obituary"
    elif any(word in text_lower for word in ['state', 'illinois', 'pritzker', 'tax', 'governor', 'grocery tax']):
        cat = "State News"
    elif any(word in text_lower for word in ['arrest', 'sheriff', 'police', 'blotter', 'jail', 'booked', 'deputy']):
        cat = "Police Report"
    elif any(word in text_lower for word in ['school', 'unit 2', 'high school', 'student', 'wolves', 'cardinals', 'gingerbread']):
        cat = "School News"
    elif any(word in text_lower for word in ['fire', 'rescue', 'structure fire', 'ems']):
        cat = "Fire & Rescue"

    found_towns = [t for t in TOWNS if re.search(fr'(?i)\b{t}\b', text)]
    
    if len(found_towns) > 1 or cat == "State News" or len(found_towns) == 0:
        town_tags = ["County News"]
    else:
        town_tags = found_towns
    
    return cat, town_tags

async def process_news():
    """Main function to run the news gathering cycle."""
    final_news, seen_hashes = [], set()
    timestamp = datetime.now().isoformat()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall("./channel/item")[:20] # Focus on top 20 for quality
                
                for item in items:
                    raw_title = item.find("title").text
                    link = item.find("link").text
                    desc = item.find("description").text or ""

                    cat, tags = get_metadata(raw_title + " " + desc)
                    if cat is None: continue 

                    # Deep Scrape for the Full Article (For Main Center)
                    full_story_text = await get_full_content(link)
                    
                    clean_title = clean_text(raw_title)
                    story_id = re.sub(r'\W+', '', clean_title).lower()
                    
                    if story_id not in seen_hashes:
                        final_news.append({
                            "id": story_id, 
                            "title": clean_title, 
                            "summary": clean_text(desc).replace('[&#8230;]', '...'),
                            "full_story": full_story_text if full_story_text else clean_text(desc),
                            "category": cat, 
                            "tags": tags, 
                            "link": f"{NEWS_CENTER_URL}#{story_id}", 
                            "date_added": timestamp
                        })
                        seen_hashes.add(story_id)
        except Exception as e: print(f"Processing Error: {e}")

    # Save to JSON
    with open(NEWS_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)
    print(f"Success: {len(final_news)} items stored. Cisne filtered.")

if __name__ == "__main__":
    asyncio.run(process_news())
