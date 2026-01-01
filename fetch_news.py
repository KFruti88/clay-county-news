import feedparser
import json
from datetime import datetime, timedelta
import time

# This tells the script where to look for Clay County news
RSS_URL = "https://news.google.com/rss/search?q=Clay+County+IL+news"

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    news_items = []
    
    # We set the look-back window to exactly 72 hours (3 days)
    cutoff = datetime.now() - timedelta(hours=72)

    for entry in feed.entries:
        # Safety check: skip entries without a valid date
        if not hasattr(entry, 'published_parsed'):
            continue
            
        published_struct = entry.published_parsed
        published_dt = datetime.fromtimestamp(time.mktime(published_struct))
        
        # Only grab stories newer than 72 hours
        if published_dt > cutoff:
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published_dt": published_dt.isoformat(),
                "published": entry.published if hasattr(entry, 'published') else "Recent",
                "source": entry.source.title if hasattr(entry, 'source') else "Local News",
                "summary": entry.summary if hasattr(entry, 'summary') else ""
            })
    
    # Sort them newest-to-oldest
    news_items.sort(key=lambda x: x.get('published_dt', ''), reverse=True)
    
    # Save the data to news.json for the website to read
    with open("news.json", "w") as f:
        json.dump(news_items, f, indent=4)

if __name__ == "__main__":
    fetch_news()
