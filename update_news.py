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
BLACKLIST = ["Cisne"]

def weld_text(text):
    """Prevents layout breaking by 'gluing' punctuation and decimals."""
    if not text: return ""
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    text = re.sub(r'(\d+)\.(\d+)', r'\1.\2', text)
    return text.strip()

def clean_text(text):
    """Removes station signatures and HTML junk."""
    if not text: return ""
    text = re.sub(r'<[^>]+>', ' ', text) # Remove HTML tags
    patterns = [
        r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)ksdk', 
        r'(?i)by\s+tom\s+lavine', r'(?i)5\s+on\s+your\s+side'
    ]
    for p in patterns: 
        text = re.sub(p, '', text)
    return weld_text(text)

async def get_full_content(url):
    """Attempts to fetch the full story text from a news URL."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10, follow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Looks for common article body tags
                content = soup.find('div', class_=['entry-content', 'article-body', 'story-text'])
                return content.get_text(separator=' ') if content else ""
    except:
        return ""
    return ""

def get_metadata(text):
    """Tags the story based on town names found in the text."""
    text_lower = text.lower()
    if any(bad.lower() in text_lower for bad in BLACKLIST):
        return None, []

    found_towns = [town for town in TOWNS if town.lower() in text_lower]
    # Default to 'Clay County' if no specific town is found
    assigned_tags = found_towns if found_towns else ["Clay County"]
    return "Local News", assigned_tags

async def process_news():
    final_news = []
    seen_ids = set()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Load sources from JSON
    try:
        with open(SOURCES_FILE, 'r') as f:
            sources = json.load(f)
    except Exception as e:
        print(f"Error loading sources.json: {e}")
        return

    async with httpx.AsyncClient() as client:
        for source in sources:
            print(f"Scraping: {source['name']}...")
            try:
                resp = await client.get(source['url'], timeout=15, follow_redirects=True)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    items = root.findall("./channel/item")[:15] # Grab top 15 from each
                    
                    for item in items:
                        title = item.find("title").text
                        link = item.find("link").text
                        desc = item.find("description").text or ""

                        # Create a unique ID based on the title
                        story_id = re.sub(r'\W+', '', title).lower()
                        if story_id in seen_ids: continue
                        seen_ids.add(story_id)

                        # Fetch deeper content if possible
                        full_text = await get_full_content(link)
                        body_content = full_text if len(full_text) > 50 else desc
                        
                        # Tagging logic
                        check_text = title + " " + body_content
                        cat, tags = get_metadata(check_text)
                        
                        if cat is None: continue # Skipped if blacklisted

                        final_news.append({
                            "id": story_id,
                            "title": clean_text(title),
                            "full_story": clean_text(body_content),
                            "tags": tags,
                            "source": source['name'],
                            "link": link,
                            "date": timestamp
                        })
            except Exception as e:
                print(f"Skipping {source['name']} due to error: {e}")

    # SAVE IN LIST FORMAT []
    with open(NEWS_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)
    
    print(f"Total stories processed: {len(final_news)}")

if __name__ == "__main__":
    asyncio.run(process_news())
