import feedparser
import json
from datetime import datetime, timedelta
import time

# This tells the script where to look for Clay County news
RSS_URL = "https://news.google.com/rss/search?q=Clay+County+IL+news"

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    news_items = []

    # 1. Set the 32-hour cutoff
    cutoff = datetime.now() - timedelta(hours=32)
    
    for entry in feed.entries:
        # Convert the RSS time format to a Python format we can compare
        published_struct = entry.published_parsed
        published_dt = datetime.fromtimestamp(time.mktime(published_struct))
        
        # 2. Only grab stories newer than 32 hours
        if published_dt > cutoff:
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published_dt": published_dt.isoformat(), # Used for sorting
                "published": entry.published if hasattr(entry, 'published') else "Recent",
                "source": entry.source.title if hasattr(entry, 'source') else "Local News",
                "summary": entry.summary if hasattr(entry, 'summary') else ""
            })
    
    # 3. Sort the list: Newest items go to index 0 (the top)
    news_items.sort(key=lambda x: x.get('published_dt', ''), reverse=True)

    # This saves the data into the file your website is looking for
    with open("news.json", "w") as f:
        json.dump(news_items, f, indent=4)

if __name__ == "__main__":
    fetch_news()
