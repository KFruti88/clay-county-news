import urllib.parse
import feedparser
import ssl
import json
import sys
import os
from datetime import datetime, timedelta
import time

def fetch_news():
    # 1. Configuration & Dates
    WNOI_RSS = "https://www.wnoi.com/category/local/feed"
    GOOGLE_BASE_URL = "https://news.google.com/rss/search?q="
    QUERY = '("Clay County IL" OR "Flora IL" OR "Louisville IL" OR "Clay City IL")'
    GOOGLE_RSS_URL = GOOGLE_BASE_URL + urllib.parse.quote(QUERY)
    
    # Calculate the cutoff for 48 hours ago
    cutoff_date = datetime.now() - timedelta(hours=48)

    # 2. Load Existing News (Persistence)
    existing_articles = []
    if os.path.exists('news_data.json'):
        with open('news_data.json', 'r') as f:
            try:
                existing_articles = json.load(f)
            except:
                existing_articles = []

    # SSL Fix
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except Exception:
        pass

    articles = []
    seen_titles = set()
    UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'

    # 3. Fetching Function with 48h Filter
    def process_feed(url, source_name):
        print(f"Checking {source_name}...")
        feed = feedparser.parse(url, agent=UA)
        count = 0
        for entry in feed.entries:
            # Parse the published date
            published_struct = getattr(entry, 'published_parsed', None)
            if published_struct:
                pub_date = datetime.fromtimestamp(time.mktime(published_struct))
                # Only keep if newer than 48 hours
                if pub_date < cutoff_date:
                    continue
            
            clean_title = entry.title.split(' - ')[0].strip()
            if clean_title.lower() not in seen_titles:
                articles.append({
                    "title": clean_title,
                    "link": entry.link,
                    "date": getattr(entry, 'published', 'Recently'),
                    "source": source_name,
                    "timestamp": time.mktime(published_struct) if published_struct else 0
                })
                seen_titles.add(clean_title.lower())
                count += 1
        print(f"Added {count} articles from {source_name}")

    # Run Fetching
    process_feed(WNOI_RSS, "WNOI Radio")
    process_feed(GOOGLE_RSS_URL, "Local News")

    # 4. Final Logic: If no new news found, keep the old news
    if not articles:
        print("No new articles in last 48h. Preserving existing news data.")
        # Optional: You could filter existing_articles here too if they are too old
        final_list = existing_articles 
    else:
        # Sort by most recent first
        articles.sort(key=lambda x: x['timestamp'], reverse=True)
        final_list = articles

    # 5. Save
    with open('news_data.json', 'w') as f:
        json.dump(final_list, f, indent=4)
    print(f"Done. Total articles in file: {len(final_list)}")

if __name__ == "__main__":
    fetch_news()
