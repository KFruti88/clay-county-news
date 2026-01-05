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
    """Turns a title into a clean ID for bookmarking (e.g., #local-news)"""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    return re.sub(r'\s+', '-', slug).strip('-')[:50]

async def get_full_content(url):
    """
    Navigates to the actual news site to grab the full text 
    so you don't get 'Read More' snippets.
    """
    try:
        async with httpx.AsyncClient() as client:
            # User-Agent makes the request look like a real browser to bypass blocks
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = await client.get(url, timeout=15, headers=headers, follow_redirects=True)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Specifically targets the full article container
                content = soup.find('div', class_='entry-content') or \
                          soup.find('article') or \
                          soup.find('div', class_='post-content')

                if content:
                    # Remove the 'Read More' buttons, scripts, and ads from the HTML
                    for element in content(['script', 'style', 'a.more-link', 'div.sharedaddy', 'div.jp-relatedposts']):
                        element.decompose()
                    
                    # Return clean text with line breaks for readability
                    return content.get_text(separator='\n', strip=True)
    except Exception as e:
        print(f"Error grabbing full content at {url}: {e}")
    return ""

async def process_news():
    final_news = []
    seen_ids = set()
    
    try:
        with open(SOURCES_FILE, 'r') as f:
            sources = json.load(f)
    except FileNotFoundError:
        print(f"Error: {SOURCES_FILE} not found.")
        return

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

                    # FETCH ACTUAL FULL STORY
                    full_text = await get_full_content(link)
                    
                    # If the scraper finds content, use it. Otherwise, use RSS description.
                    # This prevents the 'Read More' issue.
                    body = full_text if len(full_text) > 150 else (item.find("description").text or "")
                    
                    # Tagging logic
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
                    print(f"Processed: {title[:50]}...")
            except Exception as e: 
                print(f"Error processing source: {e}")

    with open(NEWS_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)
    print(f"Done! Saved {len(final_news)} articles to {NEWS_DATA_FILE}")

if __name__ == "__main__":
    asyncio.run(process_news())
