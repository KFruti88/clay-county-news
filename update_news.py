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

# Keywords to KEEP - Added 'illinois' and ' il ' to lock it to your state
CLAY_COUNTY_LOCATIONS = ["clay county", "flora", "xenia", "sailor springs", "louisville", "clay city", "illinois", " il "] #Keep Clay_County_locations

# --- NEW: Keywords to REJECT (The Blacklist) ---
# This stops statewide news that mentions Clay County only in a long list of counties
BLACKLIST = ["IAAF CONVENTION", "FAIR QUEEN", "BUS TOUR", "STATEWIDE", "ILLINOIS ASSOCIATION OF AGRICULTURAL FAIRS"]

def create_slug(text):
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    return re.sub(r'\s+', '-', slug).strip('-')[:50]

def is_strictly_local(text):
    """
    Checks if the text mentions your specific towns as whole words
    and is not part of the statewide blacklist.
    """
    text_upper = text.upper()
    # 1. Immediate rejection if any Blacklist word is found
    if any(bad_word in text_upper for bad_word in BLACKLIST):
        return False

    text_lower = text.lower()
    # 2. Check for specific towns using word boundaries (\b)
    for loc in ["flora", "xenia", "sailor springs", "louisville", "clay city", "clay county"]:
        pattern = rf"\b{re.escape(loc)}\b"
        if re.search(pattern, text_lower):
            return True
    return False

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
                    title = item.find("title").text or ""
                    link = item.find("link").text or ""
                    
                    slug = create_slug(title)
                    if slug in seen_ids: continue
                    seen_ids.add(slug)

                    full_text = await get_full_content(link)
                    # #keep full story goes to https://supportmylocalcommunity.com/local-news/
                    description = item.find("description").text if item.find("description") is not None else ""
                    body = full_text if len(full_text) > 150 else description
                    
                    search_blob = (title + " " + body)
                    
                    if is_strictly_local(search_blob):
                        # Identify which specific town it is for the tags
                        tags = [t for t in TOWNS if re.search(rf"\b{re.escape(t.lower())}\b", search_blob.lower())]
                        
                        # IMPORTANT: This link is what creates the clickable 'Read Full Story' button
                        read_more_url = f"https://supportmylocalcommunity.com/local-news/#{slug}"

                        final_news.append({
                            "id": slug,
                            "title": title,
                            "full_story": body, #keep full story goes to https://supportmylocalcommunity.com/local-news/
                            "read_more_link": read_more_url, # Key for the bookmark link
                            "link": read_more_url, # Key for compatibility with the JS engine
                            "tags": tags if tags else ["Clay County"],
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
            except Exception as e:
                print(f"Error processing source {source.get('url')}: {e}")

    with open(NEWS_DATA_FILE, 'w', encoding='utf-8') as f:
        # #keep full story goes to https://supportmylocalcommunity.com/local-news/
        json.dump(final_news, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(process_news())
