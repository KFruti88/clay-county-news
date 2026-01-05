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
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"]

def create_slug(text):
    """Turns a title into a clean ID like 'flora-festival-2026'"""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    return re.sub(r'\s+', '-', slug).strip('-')[:50]

async def get_full_content(url):
    """Fetches full article text."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10, follow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Target common news body classes
                content = soup.find('div', class_=['entry-content', 'article-body', 'story-text'])
                return content.get_text(separator=' ', strip=True) if content else ""
    except: return ""
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
                if resp.status_code != 200: continue
                
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:15]:
                    title = item.find("title").text
                    link = item.find("link").text
                    
                    slug = create_slug(title)
                    if slug in seen_ids: continue
                    seen_ids.add(slug)

                    full_text = await get_full_content(link)
                    # If full text fails, use the RSS description
                    body = full_text if len(full_text) > 100 else (item.find("description").text or "")
                    
                    # Tagging
                    found_towns = [t for t in TOWNS if t.lower() in (title + body).lower()]
                    tags = found_towns if found_towns else ["Clay County"]

                    final_news.append({
                        "id": slug,
                        "title": title,
                        "summary": body[:250] + "...",
                        "full_story": body,
                        "tags": tags,
                        "source": source['name'],
                        "link": link,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
            except Exception as e: print(f"Error: {e}")

    with open(NEWS_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_news, f, indent=4)

if __name__ == "__main__":
    asyncio.run(process_news())
