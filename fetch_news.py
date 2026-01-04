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
BLACKLIST = ["Cisne"] # Stories containing this word will be deleted instantly

def clean_text(text):
    """Removes branding, extra spaces, and HTML tags."""
    if not text: return ""
    patterns = [
        r'(?i)wnoi', 
        r'(?i)103\.9/99\.3', 
        r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', 
        r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    for p in patterns: 
        text = re.sub(p, '', text)
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def get_metadata(text):
    """Categorization with Blacklist and smart multi-town logic."""
    text_lower = text.lower()
    
    # 1. BLACKLIST CHECK
    if any(forbidden.lower() in text_lower for forbidden in BLACKLIST):
        return None, None

    cat = "General News"
    
    # 2. Category Detection
    if any(word in text_lower for word in ['musical', 'music', 'concert', 'band', 'revue']):
        cat = "Arts & Entertainment"
    elif any(word in text_lower for word in ['obituary', 'obituaries', 'passed away']):
        cat = "Obituary"
    elif any(word in text_lower for word in ['school', 'unit 2', 'high school', 'student', 'wolves', 'cardinals']):
        cat = "School News"
    elif any(word in text_lower for word in ['fire', 'rescue', 'structure fire', 'ems']):
        cat = "Fire & Rescue"
    elif any(word in text_lower for word in ['arrest', 'sheriff', 'police', 'blotter', 'deputy', 'jail']):
        cat = "Police Report"
    elif any(word in text_lower for word in ['state', 'illinois', 'springfield', 'pritzker', 'tax', 'governor', 'grocery tax']):
        cat = "State News"

    # 3. Smart Town Tagging
    found_towns = [t for t in TOWNS if re.search(fr'(?i)\b{t}\b', text)]
    
    # If it's state news or mentions more than 1 town, it's County-Wide
    if len(found_towns) > 1 or cat == "State News" or len(found_towns) == 0:
        town_tags = ["County News"]
    else:
        town_tags = found_towns
    
    return cat, town_tags

async def scrape_regional_news(query):
    """Scrapes Newsbreak/Web for additional local context."""
    scraped_stories = []
    url = f"https://www.newsbreak.com/search?q={query.replace(' ', '+')}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = await client.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for art in soup.find_all('article')[:3]:
                    title_node = art.find('h3') or art.find('a')
                    desc_node = art.find('p') or art.find('div', class_='description')
                    if title_node:
                        t_text, b_text = title_node.get_text(), (desc_node.get_text() if desc_node else "")
                        cat, tags = get_metadata(t_text + " " + b_text)
                        
                        if cat and (tags != ["County News"] or cat != "General News"):
                            scraped_stories.append({
                                "title": clean_text(t_text), 
                                "description": clean_text(b_text), 
                                "category": cat, 
                                "tags": tags
                            })
        except: pass
    return scraped_stories

async def process_news():
    """Main function to run the news gathering cycle."""
    final_news, seen_hashes = [], set()
    timestamp = datetime.now().isoformat()

    # 1. Process Local RSS
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:35]:
                    raw_title = item.find("title").text
                    desc = item.find("description").text or ""
                    
                    cat, tags = get_metadata(raw_title + " " + desc)
                    if cat is None: continue # Skip if Blacklisted

                    clean_title = clean_text(raw_title)
                    content_hash = re.sub(r'\W+', '', clean_title).lower()
                    
                    if content_hash not in seen_hashes:
                        story_id = content_hash 
                        final_news.append({
                            "id": story_id, 
                            "title": clean_title, 
                            "description": clean_text(desc),
                            "category": cat, 
                            "tags": tags, 
                            "link": f"{NEWS_CENTER_URL}#{story_id}", 
                            "date_added": timestamp
                        })
                        seen_hashes.add(content_hash)
        except Exception as e: print(f"RSS Error: {e}")

    # 2. Process Regional Web
    tasks = [scrape_regional_news(f"{t} IL news") for t in TOWNS]
    results = await asyncio.gather(*tasks)
    for result_set in results:
        for s in result_set:
            h = re.sub(r'\W+', '', s['title']).lower()
            if h not in seen_hashes:
                final_news.append({
                    "id": h, 
                    "title": s['title'], 
                    "description": s['description'],
                    "category": s['category'], 
                    "tags": s['tags'], 
                    "link": f"{NEWS_CENTER_URL}#{h}", 
                    "date_added": timestamp
                })
                seen_hashes.add(h)

    # 3. Save Output
    with open(NEWS_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)
    print(f"Success: {len(final_news)} items stored. Cisne filtered.")

if __name__ == "__main__":
    asyncio.run(process_news())
