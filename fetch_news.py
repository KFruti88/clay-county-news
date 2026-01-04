import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
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
    patterns = [r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*']
    for p in patterns: 
        text = re.sub(p, '', text)
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def get_metadata(text):
    """Detects Category, Icons (Holidays/Emergency/Video), and Town tags."""
    cat = "General News"
    icon = ""
    is_video = True if re.search(r'youtube\.com|youtu\.be', text) else False

    # Category and Holiday Mapping
    if re.search(r'(?i)\bobituary\b|\bobituaries\b|\bpassed\s*away\b', text): cat = "Obituary"; icon = "🕊️ "
    elif re.search(r'(?i)\bschool\b|\bunit\s*2\b|\bhigh\s*school\b', text): cat = "School News"; icon = "🚌 "
    elif re.search(r'(?i)christmas|xmas|santa', text): icon = "🎄 "
    elif re.search(r'(?i)valentine', text): icon = "🩷 "
    elif re.search(r'(?i)4th\s*of\s*july|fireworks', text): icon = "🎆 "
    elif re.search(r'(?i)\bstate\b|\bspringfield\b|\bidot\b', text): cat = "State News"; icon = "🏦 "
    elif re.search(r'(?i)\bfire\b|\brescue\b|\bstructure\s*fire\b', text): cat = "Fire & Rescue"; icon = "🚒 "
    elif re.search(r'(?i)\barrest\b|\bsheriff\b|\bpolice\b|\bblotter\b', text): cat = "Police Report"; icon = "🚨 "

    if is_video: icon = f"📺 {icon}"

    town_tags = [t for t in TOWNS if re.search(fr'(?i)\b{t}\b', text)]
    if not town_tags: town_tags.append("County News")
    
    return cat, town_tags, icon

async def scrape_regional_news(query):
    """Searches regional sources and applies High-Signal Filtering."""
    scraped_stories = []
    url = f"https://www.newsbreak.com/search?q={query.replace(' ', '+')}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for art in soup.find_all('article')[:3]:
                    title_node = art.find('h3') or art.find('a')
                    desc_node = art.find('p') or art.find('div', class_='description')
                    if title_node:
                        t_text = title_node.get_text()
                        b_text = desc_node.get_text() if desc_node else ""
                        cat, tags, icon = get_metadata(t_text + " " + b_text)
                        
                        # High-Signal Filter: Only keep if it's town-specific or a priority category
                        if tags != ["County News"] or cat != "General News":
                            scraped_stories.append({
                                "title": f"{icon}{clean_text(t_text)}",
                                "description": clean_text(b_text),
                                "category": cat,
                                "tags": tags
                            })
        except: pass
    return scraped_stories

async def process_news():
    """Main logic: Fetches, cleans, tags, and deduplicates news."""
    final_news = []
    seen_hashes = set()
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    timestamp = datetime.now().isoformat()

    # 1. Local RSS Processing
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_SOURCE_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:40]:
                    raw_title = item.find("title").text
                    desc = item.find("description").text or ""
                    cat, tags, icon = get_metadata(raw_title + " " + desc)
                    clean_title = f"{icon}{clean_text(raw_title)}"
                    
                    # Deduplicate using title hash
                    content_hash = re.sub(r'\W+', '', clean_title).lower()
                    if content_hash not in seen_hashes:
                        final_news.append({
                            "title": clean_title,
                            "description": clean_text(desc),
                            "category": cat,
                            "tags": tags,
                            "link": NEWS_CENTER_URL,
                            "date_added": timestamp
                        })
                        seen_hashes.add(content_hash)
        except: print("RSS Error")

    # 2. Regional Scrape Processing
    tasks = [scrape_regional_news(f"{t} IL news") for t in TOWNS]
    results = await asyncio.gather(*tasks)
    for result_set in results:
        for s in result_set:
            h = re.sub(r'\W+', '', s['title']).lower()
            if h not in seen_hashes:
                final_news.append({
                    "title": s['title'],
                    "description": s['description'],
                    "category": s['category'],
                    "tags": s['tags'],
                    "link": NEWS_CENTER_URL,
                    "date_added": timestamp
                })
                seen_hashes.add(h)

    # 3. Save as JSON
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

    print(f"Update complete. {len(final_news)} items stored.")

if __name__ == "__main__":
    asyncio.run(process_news())
