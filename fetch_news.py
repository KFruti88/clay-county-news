import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIG ---
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"]
BLACKLIST = ["Cisne"]

async def get_full_content(url):
    """Visits the actual website to grab the full article text."""
    try:
        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}, timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # WNOI specific: grabs the main article body
                article = soup.find('div', class_='entry-content')
                if article:
                    # Clean out junk
                    for tag in article.find_all(['script', 'style', 'div']):
                        if tag.get('class') and 'sharedaddy' in tag.get('class'): tag.decompose()
                    return article.get_text(separator="\n").strip()
    except: pass
    return None

def get_metadata(text):
    text_lower = text.lower()
    if any(f.lower() in text_lower for f in BLACKLIST): return None, None
    
    # Priority Categories
    if any(w in text_lower for w in ['musical', 'revue', 'concert']): cat = "Arts & Entertainment"
    elif any(w in text_lower for w in ['obituary', 'passed away']): cat = "Obituary"
    elif any(w in text_lower for w in ['school', 'fhs', 'gingerbread']): cat = "School News"
    else: cat = "General News"

    found = [t for t in TOWNS if re.search(fr'(?i)\b{t}\b', text)]
    return cat, (["County News"] if len(found) > 1 or len(found) == 0 else found)

async def process_news():
    final_news, seen_hashes = [], set()
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://www.wnoi.com/category/local/feed", timeout=15)
        root = ET.fromstring(resp.content)
        
        for item in root.findall("./channel/item")[:15]: # Processing top 15 for speed
            title = item.find("title").text
            link = item.find("link").text
            summary = item.find("description").text or ""
            
            cat, tags = get_metadata(title + " " + summary)
            if not cat: continue

            # NEW: Deep Scrape for the Full Article
            full_text = await get_full_content(link)
            
            story_id = re.sub(r'\W+', '', title).lower()
            if story_id not in seen_hashes:
                final_news.append({
                    "id": story_id,
                    "title": title.strip(),
                    "summary": summary.replace('[&#8230;]', '...').strip(),
                    "full_story": full_text if full_text else summary, # Fallback to summary if scrape fails
                    "category": cat,
                    "tags": tags,
                    "date": datetime.now().isoformat()
                })
                seen_hashes.add(story_id)

    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(process_news())
