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
# This is the main page where "Read Full Story" will jump to
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"]

def clean_text(text):
    """Removes branding, extra spaces, and HTML tags for a professional look."""
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
    """Categorizes the story and identifies the town for mascot logic."""
    cat = "General News"
    if re.search(r'(?i)\bobituary\b|\bobituaries\b|\bpassed\s*away\b', text): cat = "Obituary"
    elif re.search(r'(?i)\bschool\b|\bunit\s*2\b|\bhigh\s*school\b', text): cat = "School News"
    elif re.search(r'(?i)\bfire\b|\brescue\b|\bstructure\s*fire\b', text): cat = "Fire & Rescue"
    elif re.search(r'(?i)\barrest\b|\bsheriff\b|\bpolice\b|\bblotter\b', text): cat = "Police Report"

    town_tags = [t for t in TOWNS if re.search(fr'(?i)\b{t}\b', text)]
    if not town_tags: 
        town_tags.append("County News")
    
    return cat, town_tags

async def scrape_regional_news(query):
    """Searches external sources to find high-signal local news."""
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
                        t_text = title_node.get_text()
                        b_text = desc_node.get_text() if desc_node else ""
                        cat, tags = get_metadata(t_text + " " + b_text)
                        if tags != ["County News"] or cat != "General News":
                            scraped_stories.append({
                                "title": clean_text(t_text),
                                "description": clean_text(b_text),
                                "category": cat,
                                "tags": tags
                            })
        except: pass
    return scraped_stories

async def process_news():
    """Main function to gather, clean, and deduplicate all news."""
    final_news = []
    seen_hashes = set()
    timestamp = datetime.now().isoformat()

    # 1. Fetch Local RSS
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:30]:
                    raw_title = item.find("title").text
                    desc = item.find("description").text or ""
                    cat, tags = get_metadata(raw_title + " " + desc)
                    clean_title = clean_text(raw_title)
                    
                    # Deduplication & ID Generation
                    content_hash = re.sub(r'\W+', '', clean_title).lower()
                    if content_hash not in seen_hashes:
                        # Create unique Bookmark ID
                        story_id = content_hash 
                        
                        final_news.append({
                            "id": story_id,
                            "title": clean_title,
                            "description": clean_text(desc),
                            "category": cat,
                            "tags": tags,
                            "link": f"{NEWS_CENTER_URL}#{story_id}", # Deep Link
                            "date_added": timestamp
                        })
                        seen_hashes.add(content_hash)
        except: print("Error fetching local RSS")

    # 2. Run Regional Searches
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

    # 3. Final Output to JSON
    with open(NEWS_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)

    print(f"Success: {len(final_news)} items stored.")

if __name__ == "__main__":
    asyncio.run(process_news())
