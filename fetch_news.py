import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
FEED_XML_FILE = 'feed.xml'              
NEWS_DATA_FILE = 'news_data.json'        
RSS_SOURCE_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"]

def clean_text(text):
    """Scrub branding, frequencies, and leading dates for a clean display."""
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
    """Detects Category, Icons (Holidays/State/School/Video), and Town tags."""
    cat = "General News"
    icon = ""
    
    # --- 1. VIDEO DETECTION ---
    is_video = False
    if re.search(r'youtube\.com|youtu\.be', text):
        is_video = True

    # --- 2. CATEGORY & HOLIDAY DETECTION ---
    if re.search(r'(?i)\bobituary\b|\bobituaries\b|\bpassed\s*away\b|\bdeath\s*notice\b', text):
        cat = "Obituary"; icon = "🕊️ "
    elif re.search(r'(?i)\bschool\b|\bunit\s*2\b|\bhigh\s*school\b|\bgrade\s*school\b|\bteacher\b', text):
        cat = "School News"; icon = "🚌 "
    elif re.search(r'(?i)christmas|xmas|santa|yuletide', text):
        icon = "🎄 "
    elif re.search(r'(?i)valentine|sweetheart', text):
        icon = "🩷 "
    elif re.search(r'(?i)4th\s*of\s*july|july\s*4th|independence\s*day|fireworks', text):
        icon = "🎆 "
    elif re.search(r'(?i)\bstate\b|\bspringfield\b|\bpritzker\b|\bidot\b', text):
        cat = "State News"; icon = "🏦 "
    elif re.search(r'(?i)\bfire\b|\brescue\b|\bextrication\b|\bstructure\s*fire\b|\bmutual\s*aid\b', text):
        cat = "Fire & Rescue"; icon = "🚒 "
    elif re.search(r'(?i)\barrest\b|\bsheriff\b|\bpolice\b|\bbooking\b|\bcourt\s*news\b|\bblotter\b', text):
        cat = "Police Report"; icon = "🚨 "

    # Add Video Icon if YouTube is present
    if is_video:
        icon = f"📺 {icon}"

    # --- 3. MULTI-TOWN TAGGING ---
    town_tags = []
    town_map = {
        "Flora": r'(?i)\bflora\b',
        "Xenia": r'(?i)\bxenia\b',
        "Louisville": r'(?i)\blouisville\b',
        "Clay City": r'(?i)clay\s*city',
        "Sailor Springs": r'(?i)sailor\s*springs'
    }
    
    for town, pattern in town_map.items():
        if re.search(pattern, text):
            town_tags.append(town)
    
    # Fallback to "County News" if no town is identified
    if not town_tags:
        town_tags.append("County News")
            
    return cat, town_tags, icon

async def scrape_regional_news(query):
    """Searches regional NewsBreak and applies multi-tagging."""
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
                        title_text = title_node.get_text()
                        body_text = desc_node.get_text() if desc_node else ""
                        full_content = title_text + " " + body_text
                        
                        cat, tags, icon = get_metadata(full_content)
                        # RELEVANCE FILTER: Must mention a specific town OR have a special category
                        if tags != ["County News"] or cat != "General News":
                            scraped_stories.append({
                                "title": f"{icon}{clean_text(title_text)}",
                                "description": clean_text(body_text),
                                "category": cat,
                                "tags": tags
                            })
        except: pass
    return scraped_stories

async def process_news():
    """Main logic: Fetches news, tags, and deduplicates."""
    final_news = []
    seen_hashes = set() 
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    timestamp = datetime.now().isoformat()

    # 1. Local RSS
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
                for item in root.findall("./channel/item")[:40]:
                    raw_title = item.find("title").text
                    content_node = item.find("content:encoded", namespaces)
                    full_text = content_node.text if content_node is not None else (item.find("description").text or "")
                    
                    cat, tags, icon = get_metadata(raw_title + " " + full_text)
                    clean_title = f"{icon}{clean_text(raw_title)}"
                    
                    content_hash = re.sub(r'\W+', '', clean_title).lower()
                    if content_hash not in seen_hashes:
                        final_news.append({
                            "title": clean_title,
                            "description": clean_text(full_text),
                            "category": cat,
                            "tags": tags,
                            "link": NEWS_CENTER_URL,
                            "date_added": timestamp
                        })
                        seen_hashes.add(content_hash)
        except: print("Local RSS source unavailable.")

    # 2. Regional Scrape
    search_tasks = []
    for town in TOWNS:
        search_tasks.append(scrape_regional_news(f"{town} IL news"))
        search_tasks.append(scrape_regional_news(f"{town} IL fire rescue police"))
        search_tasks.append(scrape_regional_news(f"{town} IL obituaries"))

    regional_results = await asyncio.gather(*search_tasks)
    for result_set in regional_results:
        for s in result_set:
            content_hash = re.sub(r'\W+', '', s['title']).lower()
            if content_hash not in seen_hashes:
                final_news.append({
                    "title": s['title'],
                    "description": s['description'],
                    "category": s['category'],
                    "tags": s['tags'],
                    "link": NEWS_CENTER_URL,
                    "date_added": timestamp
                })
                seen_hashes.add(content_hash)

    # 3. Save as JSON with UTF-8
    with open(NEWS_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(final_news, f, indent=4, ensure_ascii=False)

    # 4. Save as RSS XML
    rss_items = ""
    for item in final_news:
        town_label = ", ".join(item['tags'])
        rss_items += f"""
        <item>
            <title>{item['title']}</title>
            <link>{item['link']}</link>
            <description>[{town_label} - {item['category']}] {item['description'][:250]}...</description>
            <pubDate>{pub_date}</pubDate>
        </item>"""
    
    rss_feed = f'<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0"><channel><title>Clay County News Center</title><link>{NEWS_CENTER_URL}</link><description>Combined Local and Regional Updates</description>{rss_items}</channel></rss>'
    
    with open(FEED_XML_FILE, 'w', encoding='utf-8') as f:
        f.write(rss_feed)

    print(f"Update complete. {len(final_news)} unique items stored.")

if __name__ == "__main__":
    asyncio.run(process_news())
