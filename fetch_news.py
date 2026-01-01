import feedparser
import json
from datetime import datetime, timedelta
import time

# This query tells Google to specifically find articles from NewsBreak's 
# location pages for your towns.
SEARCH_QUERY = (
    "site:newsbreak.com/louisville-il OR "
    "site:newsbreak.com/flora-il OR "
    "site:newsbreak.com/clay-city-il OR "
    "site:newsbreak.com/sailor-springs-il OR "
    "site:newsbreak.com/xenia-il OR "
    "site:newsbreak.com/iola-il OR "
    "Clay County IL news"
)

RSS_URL = f"https://news.google.com/rss/search?q={SEARCH_QUERY}"

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    news_items = []
    
    # Keeping the 7-day window to ensure the feed stays full
    cutoff = datetime.now() - timedelta(hours=168)

    for entry in feed.entries:
        if not hasattr(entry, 'published_parsed'):
            continue
            
        published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        
        if published_dt > cutoff:
            # Clean up source names
            source_name = entry.source.title if hasattr(entry, 'source') else "Local News"
            if "newsbreak" in source_name.lower():
                source_name = "NewsBreak"

            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published_dt": published_dt.isoformat(),
                "published": entry.published,
                "source": source_name,
                "summary": entry.summary if hasattr(entry, 'summary') else ""
            })
    
    # Remove duplicates (sometimes Google finds the same story twice)
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
