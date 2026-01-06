import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
NEWS_DATA_FILE = 'news_data.json'
SOURCES_FILE = 'sources.json' 
# #keep full story goes to https://supportmylocalcommunity.com/local-news/
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"] #Keep Towns
CLAY_COUNTY_LOCATIONS = ["clay county", "flora", "xenia", "sailor springs", "louisville", "clay city"] #Keep Clay_County_locations

def create_slug(text):
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    return re.sub(r'\s+', '-', slug).strip('-')[:50]

async def get_full_content(url):
    """ #keep full story goes to https://supportmylocalcommunity.com/local-news/ """
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
                    for noise in content(['script', 'style', 'a', 'div.sharedaddy', 'div.jp-relatedposts', 'div.wpcnt']):
                        noise.decompose()
                    # #keep full story goes to https://supportmylocalcommunity.com/local-news/
                    return content.get_text(separator='\n', strip=True)
    except: pass
    return ""

async def process_news():
    final_news = []
    seen_ids = set()
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
                    # #keep full story goes to https://supportmylocalcommunity.com/local-news/
                    body = full_text if len(full_text) > 150 else (item.find("description").text or "")
                    
                    if any(loc in (title + body).lower() for loc in CLAY_COUNTY_LOCATIONS):
                        tags = [t for t in TOWNS if t.lower() in (title + body).lower()]
                        final_news.append({
                            "id": slug,
                            "title": title,
                            "full_story": body, #keep full story goes to https://supportmylocalcommunity.com/local-news/
                            "tags": tags if tags else ["Clay County"],
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
            except: pass

    with open(NEWS_DATA_FILE, 'w', encoding='utf-8') as f:
        # #keep full story goes to https://supportmylocalcommunity.com/local-news/
        json.dump(final_news, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(process_news())
