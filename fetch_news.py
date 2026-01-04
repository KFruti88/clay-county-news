import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
CALENDAR_JSON_FILE = "calendar_events.json"
FEED_XML_FILE = 'feed.xml'
RSS_SOURCE_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

# List of towns to watch for across ALL sources
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"]
# States to monitor for mentions (used in the search queries)
REGIONAL_STATES = ["IL", "Illinois", "Missouri", "MO", "Indiana", "IN", "Kentucky", "KY"]

# --- COLOR THEMES ---
THEMES = {
    "Clay City": {"bg": "#ADD8E6", "text": "#000000"},
    "Sailor Springs": {"bg": "#367C2B", "text": "#FFDE00"},
    "Xenia": {"bg": "#0077BE", "text": "#FFC0CB"},
    "Flora": {"bg": "#FFFFFF", "text": "#000000"},
    "Louisville": {"bg": "#FFFFFF", "text": "#000000"},
    "General News": {"bg": "#808080", "text": "#FFFFFF"}
}

def clean_text(text):
    if not text: return ""
    patterns = [r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*']
    for p in patterns:
        text = re.sub(p, '', text)
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def get_primary_town(text):
    """Deep search for town mentions in any text block."""
    town_map = {
        "Flora": r'(?i)\bflora\b',
        "Xenia": r'(?i)\bxenia\b',
        "Louisville": r'(?i)\blouisville\b',
        "Clay City": r'(?i)clay\s*city',
        "Sailor Springs": r'(?i)sailor\s*springs'
    }
    for town, pattern in town_map.items():
        if re.search(pattern, text):
            return town
    return "General News"

async def scrape_regional_news(query):
    """Expanded scraper to search regional NewsBreak for specific town mentions."""
    scraped_stories = []
    # Search query specifically targets the town within the state/region
    url = f"https://www.newsbreak.com/search?q={query.replace(' ', '+')}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = await client.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for art in soup.find_all('article')[:3]:
                    title_node = art.find('h3') or art.find('a')
                    desc_node = art.find('p') or art.find('div', class_='description')
                    if title_node:
                        title_text = title_node.get_text()
                        body_text = desc_node.get_text() if desc_node else ""
                        full_content = title_text + " " + body_text
                        
                        # Only keep the story if it specifically mentions one of our towns
                        detected_town = get_primary_town(full_content)
                        if detected_town != "General News":
                            scraped_stories.append({
                                "title": clean_text(title_text),
                                "full_text": clean_text(body_text) or f"Regional update mentioning {detected_town}.",
                                "town": detected_town
                            })
        except: pass
    return scraped_stories

async def process_news():
    stories = []
    seen_content = set()
    today_iso = datetime.now().strftime('%Y-%m-%d')
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    # 1. Fetch Local RSS (WNOI)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
                for item in root.findall("./channel/item")[:40]:
                    title = item.find("title").text
                    content_node = item.find("content:encoded", namespaces)
                    full_text = content_node.text if content_node is not None else (item.find("description").text or "")
                    
                    town_tag = get_primary_town(full_text)
                    clean_title = clean_text(title)
                    
                    unique_key = clean_title if town_tag == "General News" else (clean_title + town_tag)
                    if unique_key not in seen_content:
                        stories.append({"title": clean_title, "desc": clean_text(full_text), "town": town_tag})
                        seen_content.add(unique_key)
        except: print("RSS source unavailable.")

    # 2. Regional/State Supplemental Scrape
    # We create search queries for each town across the multi-state region
    search_tasks = []
    for town in TOWNS:
        # This searches for "Town Name Illinois", "Town Name Missouri", etc.
        search_tasks.append(scrape_regional_news(f"{town} IL news"))
        search_tasks.append(scrape_regional_news(f"{town} news regional Midwest"))

    regional_results = await asyncio.gather(*search_tasks)
    for result_set in regional_results:
        for s in result_set:
            if s['title'] not in seen_content:
                stories.append({"title": s['title'], "desc": s['full_text'], "town": s['town']})
                seen_content.add(s['title'])

    # 3. Output Generation
    final_json = []
    rss_items_xml = ""
    for s in stories:
        final_json.append({
            "title": s['title'],
            "start": today_iso,
            "description": s['desc'],
            "url": NEWS_CENTER_URL,
            "backgroundColor": THEMES[s['town']]["bg"],
            "textColor": THEMES[s['town']]["text"],
            "extendedProps": {"town": s['town']}
        })
        rss_items_xml += f"<item><title>{s['title']}</title><link>{NEWS_CENTER_URL}</link><description>{s['desc'][:200]}...</description><pubDate>{pub_date}</pubDate></item>"

    with open(CALENDAR_JSON_FILE, "w") as f: json.dump(final_json, f, indent=4)
    with open(FEED_XML_FILE, 'w') as f: f.write(f'<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0"><channel><title>Clay County Regional News</title>{rss_items_xml}</channel></rss>')

    print(f"Update complete. Total items: {len(final_json)}")

if __name__ == "__main__":
    asyncio.run(process_news())
