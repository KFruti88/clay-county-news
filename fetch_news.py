import httpx
import asyncio
import json
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from copy import deepcopy

# --- CONFIGURATION ---
DATA_EXPORT_FILE = "news_data.json"
SMALL_TOWNS = ["Clay City", "Xenia", "Sailor Springs"]
TOWNS = ["Flora", "Louisville"] + SMALL_TOWNS
RSS_URL = "https://www.wnoi.com/category/local/feed"
NEWS_CENTER_URL = "https://supportmylocalcommunity.com/clay-county-news-center/"

# --- COLOR THEMES ---
THEMES = {
    "Clay City": {"bg": "#ADD8E6", "text": "#000000"},      # Light Blue / Black
    "Sailor Springs": {"bg": "#367C2B", "text": "#FFDE00"}, # JD Green / JD Yellow
    "Xenia": {"bg": "#0077BE", "text": "#FFC0CB"},          # Ocean Blue / Pink
    "Flora": {"bg": "#FFFFFF", "text": "#000000"},          # Default White/Black
    "Louisville": {"bg": "#FFFFFF", "text": "#000000"},     # Default White/Black
    "General": {"bg": "#F4F4F4", "text": "#333333"}         # Soft Grey for County News
}

def clean_text(text):
    """Scrub branding, frequencies, and HTML tags."""
    if not text: return ""
    patterns = [
        r'(?i)wnoi', r'(?i)103\.9/99\.3', r'(?i)local\s*--', 
        r'(?i)by\s+tom\s+lavine', r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    for p in patterns:
        text = re.sub(p, '', text)
    # Remove HTML tags and extra whitespace
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def get_primary_town(text):
    """Identifies the primary town or defaults to General."""
    if not text: return "General"
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
    return "General"

async def fetch_rss():
    """Fetches RSS feed and assigns town_tags and themes."""
    stories = []
    namespaces = {'content': 'http://purl.org/rss/1.0/modules/content/'}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(RSS_URL, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:30]:
                    title = item.find("title").text
                    brief = item.find("description").text or ""
                    content_node = item.find("content:encoded", namespaces)
                    full_text = content_node.text if content_node is not None else brief

                    town_tag = get_primary_town(title + " " + full_text)
                    stories.append({
                        "title": clean_text(title),
                        "brief": clean_text(brief)[:180] + "...",
                        "full_story": clean_text(full_text),
                        "link": NEWS_CENTER_URL,
                        "town_tag": town_tag,
                        "theme": THEMES.get(town_tag, THEMES["General"])
                    })
        except Exception as e:
            print(f"RSS Error: {e}")
    return stories

async def scrape_town(town):
    """Scrapes NewsBreak for town-specific updates."""
    stories = []
    url = f"https://www.newsbreak.com/search?q={town}+IL+news"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for art in soup.find_all('article')[:3]:
                    title_node = art.find('h3') or art.find('a')
                    if title_node:
                        stories.append({
                            "title": clean_text(title_node.get_text()),
                            "brief": f"Community update for {town}.",
                            "full_story": f"Detailed community updates for {town}.",
                            "link": NEWS_CENTER_URL,
                            "town_tag": town,
                            "theme": THEMES.get(town, THEMES["General"])
                        })
        except Exception as e:
            print(f"Scrape Error for {town}: {e}")
    return stories

async def run():
    seen_stories = {}
    print("Gathering news and applying themes...")

    # 1. Process RSS (Regional News)
    rss_stories = await fetch_rss()
    for s in rss_stories:
        seen_stories[s['title']] = s

    # 2. Process Town Scrapes
    for town in TOWNS:
        print(f"Checking {town}...")
        scraped = await scrape_town(town)
        for s in scraped:
            if s['title'] not in seen_stories:
                seen_stories[s['title']] = s

    # 3. Apply Fallback Logic for Small Towns
    unique_list = list(seen_stories.values())
    final_output = []
    
    for town in TOWNS:
        # Filter news items specifically tagged for this town
        town_news = [s for s in unique_list if s['town_tag'] == town]
        
        if town in SMALL_TOWNS and not town_news:
            # If no local news, duplicate General news with town's specific theme
            general_news = [s for s in unique_list if s['town_tag'] == "General"]
            for g in general_news:
                fallback = deepcopy(g)
                fallback['town_tag'] = town
                fallback['theme'] = THEMES[town]
                final_output.append(fallback)
        else:
            final_output.extend(town_news)

    # 4. Save to JSON
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(final_output, f, indent=4)

    print(f"Update complete! Saved {len(final_output)} themed entries to {DATA_EXPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(run())
