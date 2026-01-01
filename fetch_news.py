import feedparser
import json
from datetime import datetime, timedelta
import time

# 1. The Strict Filter List
CLAY_COUNTY_TOWNS = ['flora', 'clay city', 'louisville', 'sailor springs', 'xenia', 'iola', 'clay county']

# 2. Broad Search to catch mentions in regional hubs
SEARCH_QUERY = (
    "site:newsbreak.com/louisville-il OR site:newsbreak.com/flora-il OR "
    "site:newsbreak.com/clay-city-il OR site:newsbreak.com/sailor-springs-il OR "
    "site:newsbreak.com/xenia-il OR site:newsbreak.com/iola-il OR "
    "\"Effingham\" OR \"Fairfield\" OR \"Salem\" OR \"Mt. Vernon\" OR \"Clay County\""
)

RSS_URL = f"https://news.google.com/rss/search?q={SEARCH_QUERY}"

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    news_items = []
    cutoff = datetime.now() - timedelta(hours=168) # 7-day window

    for entry in feed.entries:
        if not hasattr(entry, 'published_parsed'):
            continue
            
        published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        
        if published_dt > cutoff:
            title = entry.title
            summary = entry.summary if hasattr(entry, 'summary') else ""
            content_to_check = (title + " " + summary).lower()

            # --- THE STRICT FILTER ---
            # Only proceed if one of YOUR towns is actually mentioned in the text
            if any(town in content_to_check for town in CLAY_COUNTY_TOWNS):
                
                source_name = entry.source.title if hasattr(entry, 'source') else "Local News"
                if "newsbreak" in source_name.lower():
                    source_name = "NewsBreak"

                news_items.append({
                    "title": title,
                    "link": entry.link,
                    "published_dt": published_dt.isoformat(),
                    "published": entry.published,
                    "source": source_name,
                    "summary": summary
                })
    
    # Deduplicate and Sort
    seen_titles = set()
    unique_items = []
    for item in news_items:
        if item['title'] not in seen_titles:
            unique_items.append(item)
            seen_titles.add(item['title'])

    unique_items.sort(key=lambda x: x.get('published_dt', ''), reverse=True)
    
    with open("news.json", "w") as f:
        json.dump(unique_items, f, indent=4)

if __name__ == "__main__":
    fetch_news()
