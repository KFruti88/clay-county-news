import feedparser
import json

# This tells the script where to look for Clay County news
RSS_URL = "https://news.google.com/rss/search?q=Clay+County+IL+news"

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    news_items = []
    
    # We take the 20 most recent stories
    for entry in feed.entries[:20]:
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published if hasattr(entry, 'published') else "Recent",
            "source": entry.source.title if hasattr(entry, 'source') else "Local News",
            "summary": entry.summary if hasattr(entry, 'summary') else ""
        })
    
    # This saves the data into the file your website is looking for
    with open("news.json", "w") as f:
        json.dump(news_items, f, indent=4)

if __name__ == "__main__":
    fetch_news()
