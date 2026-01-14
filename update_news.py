import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup
import os

# --- CONFIGURATION ---
NEWS_DATA_FILE = 'news_data.json'
SOURCES_FILE = 'sources.json' 
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"] 
CLAY_COUNTY_LOCATIONS = ["clay county", "flora", "xenia", "sailor springs", "louisville", "clay city", "illinois", " il "]
BLACKLIST = ["IAAF CONVENTION", "FAIR QUEEN", "BUS TOUR", "STATEWIDE", "ILLINOIS ASSOCIATION OF AGRICULTURAL FAIRS"]

def create_slug(text):
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    return re.sub(r'\s+', '-', slug).strip('-')[:50]

def is_strictly_local(text):
    text_upper = text.upper()
    if any(bad_word in text_upper for bad_word in BLACKLIST):
        return False
    text_lower = text.lower()
    for loc in ["flora", "xenia", "sailor springs", "louisville", "clay city", "clay county"]:
        pattern = rf"\b{re.escape(loc)}\b"
        if re.search(pattern, text_lower):
            return True
    return False

async def get_full_content_and_image(url):
    """ Fetches story body AND looks for a featured image on the page """
    result = {"body": "", "image": ""}
    try:
        async with httpx.AsyncClient() as client:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = await client.get(url, timeout=10, headers=headers, follow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Grab the image (Open Graph image used by most news sites)
                og_image = soup.find("meta", property="og:image")
                if og_image:
                    result["image"] = og_image["content"]
                
                # Grab the body text
                content = soup.find('div', class_='entry-content') or \
                          soup.find('article') or \
                          soup.find('div', class_='post-content')
                if content:
                    for noise in content(['script', 'style', 'a', 'div.sharedaddy', 'div.jp-relatedposts', 'div.wpcnt']):
                        noise.decompose()
                    result["body"] = content.get_text(separator='\n', strip=True)
    except: pass
    return result

async def process_news():
    # 1. Load EXISTING news
    existing_news = []
    seen_ids = set()
    if os.path.exists(NEWS_DATA_FILE):
        try:
            with open(NEWS_DATA_FILE, 'r', encoding='utf-8') as f:
                existing_news = json.load(f)
                seen_ids = {article['id'] for article in existing_news}
        except:
            existing_news = []

    new_articles_count = 0
    with open(SOURCES_FILE, 'r') as f:
        all_sources = json.load(f)

    # Priority: WNOI first
    primary_sources = [s for s in all_sources if "wnoi" in s['url'].lower()]
    secondary_sources = [s for s in all_sources if "wnoi" not in s['url'].lower()]
    ordered_sources = primary_sources + secondary_sources

    async with httpx.AsyncClient() as client:
        for source in ordered_sources:
            is_primary = "wnoi" in source['url'].lower()
            try:
                resp = await client.get(source['url'], timeout=15)
                root = ET.fromstring(resp.content)
                limit = 30 if is_primary else 15
                
                for item in root.findall("./channel/item")[:limit]:
                    title = item.find("title").text or ""
                    link = item.find("link").text or ""
                    slug = create_slug(title)

                    if slug in seen_ids: continue

                    # Fetch the content and the image
                    content_data = await get_full_content_and_image(link)
                    description = item.find("description").text if item.find("description") is not None else ""
                    body = content_data["body"] if len(content_data["body"]) > 150 else description
                    
                    search_blob = (title + " " + body)
                    
                    if is_primary or is_strictly_local(search_blob):
                        seen_ids.add(slug)
                        
                        # --- DYNAMIC TAGGING (Obit, Fire, Police) ---
                        tags = [t for t in TOWNS if re.search(rf"\b{re.escape(t.lower())}\b", search_blob.lower())]
                        
                        if any(word in search_blob.lower() for word in ["obituary", "funeral", "passed away", "memorial service"]):
                            tags.append("Obituary")
                        if any(word in search_blob.lower() for word in ["fire department", "firefighters", "blaze", "structure fire"]):
                            tags.append("Fire Dept")
                        if any(word in search_blob.lower() for word in ["police", "sheriff", "arrested", "deputy", "dispatch"]):
                            tags.append("Police/PD")
                            
                        read_more_url = f"https://supportmylocalcommunity.com/local-news/#{slug}"

                        existing_news.append({
                            "id": slug,
                            "title": title,
                            "image": content_data["image"],
                            "full_story": body,
                            "read_more_link": read_more_url,
                            "link": read_more_url,
                            "tags": list(set(tags)) if tags else ["Clay County"],
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "is_primary": is_primary
                        })
                        new_articles_count += 1
            except:
                continue

    # 2. Sort and Save
    existing_news.sort(key=lambda x: x['date'], reverse=True)
    with open(NEWS_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_news, f, indent=4, ensure_ascii=False)
    
    print(f"Update complete. Added {new_articles_count} new articles.")

if __name__ == "__main__":
    asyncio.run(process_news())
