import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
NEWS_DATA_FILE = 'news_data.json'
SOURCES_FILE = 'sources.json' # KEEPING THIS FILE AS REQUESTED
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"]
CLAY_COUNTY_LOCATIONS = ["clay county", "flora", "xenia", "sailor springs", "louisville", "clay city"]

def create_slug(text):
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    return re.sub(r'\s+', '-', slug).strip('-')[:50]

async def get_full_content(url):
    try:
        async with httpx.AsyncClient() as client:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = await client.get(url, timeout=15, headers=headers, follow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                content = soup.find('div', class_='entry-content') or \
                          soup.find('article') or \
                          soup.find('div', class_='post-content')
                if content:
                    for noise in content(['script', 'style', 'a.more-link', 'div.sharedaddy', 'div.jp-relatedposts', 'div.wpcnt']):
                        noise.decompose()
                    for a in content.find_all('a'):
                        if "read more" in a.text.lower():
                            a.decompose()
                    return content.get_text(separator='\n', strip=True)
    except: pass
    return ""

async def process_news():
    final_news = []
    seen_ids = set()
    
    # Reads from your sources.json to find where to scrape
    with open(SOURCES_FILE, 'r') as f:
        sources = json.load(f)

    async with httpx.AsyncClient() as client:
        for source in sources:
            try:
                resp = await client.get(source['url'], timeout=15)
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:15]:
                    title = item.find("title").text
                    link = item.find("link").text
                    slug = create_slug(title)
                    if slug in seen_ids: continue
                    seen_ids.add(slug)

                    full_text = await get_full_content(link)
                    body = full_text if len(full_text) > 150 else (item.find("description").text or "")
                    search_text = (title + " " + body).lower()
                    
                    if any(loc in search_text for loc in CLAY_COUNTY_LOCATIONS):
                        tags = [t for t in TOWNS if t.lower() in search_text]
                        
                        # DATA SAVED WITHOUT "SOURCE" NAME
                        final_news.append({
                            "id": slug,
                            "title": title,
                            "full_story": body, 
                            "tags": tags if tags else ["Clay County"],
                            "link": link,
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
            except: pass

    with open(NEWS_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(process_news())
