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
# These are the towns used for tagging and the mandatory filter
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"]
CLAY_COUNTY_LOCATIONS = ["clay county", "flora", "xenia", "sailor springs", "louisville", "clay city"]

def create_slug(text):
    """Turns a title into a clean ID for bookmarking"""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    return re.sub(r'\s+', '-', slug).strip('-')[:50]

async def get_full_content(url):
    """
    Navigates to the source, grabs ONLY the article body, 
    and deletes 'Read More' or social links.
    """
    try:
        async with httpx.AsyncClient() as client:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = await client.get(url, timeout=15, headers=headers, follow_redirects=True)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Target the main article body
                content = soup.find('div', class_='entry-content') or \
                          soup.find('article') or \
                          soup.find('div', class_='post-content')

                if content:
                    # REMOVE "READ MORE" AND SOURCE NOISE
                    for noise in content(['script', 'style', 'a.more-link', 'div.sharedaddy', 'div.jp-relatedposts', 'div.wpcnt']):
                        noise.decompose()
                    
                    # Specifically remove any links matching "Read More" text
                    for a in content.find_all('a'):
                        if "read more" in a.text.lower():
                            a.decompose()
                    
                    return content.get_text(separator='\n', strip=True)
    except Exception as e:
        print(f"Error grabbing content: {e}")
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
                    
                    # Ensure we have the full text, fallback to description if scrape fails
                    body = full_text if len(full_text) > 150 else (item.find("description").text or "")
                    
                    # --- NEW FILTER LOGIC ---
                    # Combine title and body to search for your mandatory locations
                    search_text = (title + " " + body).lower()
                    
                    # ONLY proceed if the story mentions Clay County or the specific towns
                    if any(location in search_text for location in CLAY_COUNTY_LOCATIONS):
                        # Tagging logic for town pages
                        found_towns = [t for t in TOWNS if t.lower() in search_text]
                        tags = found_towns if found_towns else ["Clay County"]

                        final_news.append({
                            "id": slug,
                            "title": title,
                            "full_story": body, 
                            "tags": tags,
                            "link": link,
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
                        print(f"Kept (Local): {title[:50]}...")
                    else:
                        print(f"Skipped (Not Local): {title[:50]}...")
                        
            except Exception as e: 
                print(f"Error: {e}")

    with open(NEWS_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)
    print(f"Success! {len(final_news)} local stories saved to {NEWS_DATA_FILE}")

if __name__ == "__main__":
    asyncio.run(process_news())
