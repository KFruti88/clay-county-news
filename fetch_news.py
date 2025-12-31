import feedparser
import json
from datetime import datetime, timedelta
import time

RSS_URL = "https://news.google.com/rss/search?q=Clay+County+IL+news"

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    news_items = []
    cutoff = datetime.now() - timedelta(hours=32)
    
    for entry in feed.entries:
        published_struct = entry.published_parsed
        published_dt = datetime.fromtimestamp(time.mktime(published_struct))
        
        if published_dt > cutoff:
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published_dt": published_dt.isoformat(),
                "published": entry.published if hasattr(entry, 'published') else "Recent",
                "source": entry.source.title if hasattr(entry, 'source') else "Local News",
                "summary": entry.summary if hasattr(entry, 'summary') else ""
            })
    
    news_items.sort(key=lambda x: x.get('published_dt', ''), reverse=True)
    with open("news.json", "w") as f:
        json.dump(news_items, f, indent=4)

if __name__ == "__main__":
    fetch_news()
