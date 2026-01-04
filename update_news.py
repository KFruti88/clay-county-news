import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

# --- CONFIGURATION ---
JSON_FILE = "news_data.json"
TOWNS = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs", "Clay County"]

# List of URLs to monitor
SOURCES = [
    {"url": "https://www.effinghamradio.com/local-news/", "tag": "Regional"},
    {"url": "https://www.wfiwradio.com/local-news/", "tag": "Regional"},
    {"url": "https://freedom929.com/category/local-news/", "tag": "Regional"},
    {"url": "https://www.frankandbright.com/", "tag": "Obituaries"},
    {"url": "http://www.kistler-patterson.com/obituaries/obituary-listings", "tag": "Obituaries"},
    {"url": "https://www.wnoi.com/category/general-news/", "tag": "General News"}
]

def generate_slug(title):
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug

def get_town_tags(text):
    found_tags = [town for town in TOWNS if town.lower() in text.lower()]
    return found_tags if found_tags else ["County News"]

def fetch_and_filter():
    all_news = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for source in SOURCES:
        try:
            print(f"Checking {source['url']}...")
            res = requests.get(source['url'], headers=headers, timeout=10)
            if res.status_code != 200: continue
            
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # This logic finds headlines (h2/h3) and nearby paragraphs
            for item in soup.find_all(['article', 'div'], class_=re.compile('post|entry|item|obituary')):
                title_el = item.find(['h2', 'h3', 'a'])
                if not title_el: continue
                title = title_el.text.strip()
                
                # Filter: Only keep if it mentions your towns/county
                story_text = item.text.strip()
                if any(town.lower() in story_text.lower() for town in TOWNS):
                    
                    category = source['tag']
                    # Smart category override
                    if "obituary" in story_text.lower(): category = "Obituaries"
                    if "fire" in story_text.lower() or "police" in story_text.lower(): category = "Police & Fire"

                    news_entry = {
                        "title": title,
                        "slug": generate_slug(title),
                        "full_story": story_text[:1000], # Keep it concise
                        "category": category,
                        "tags": get_town_tags(story_text),
                        "date_added": datetime.now().isoformat()
                    }
                    all_news.append(news_entry)
        except Exception as e:
            print(f"Error on {source['url']}: {e}")
            
    return all_news

if __name__ == "__main__":
    latest_news = fetch_and_filter()
    # Save the results
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(latest_news, f, indent=4, ensure_ascii=False)
    print("News Sync Complete.")
