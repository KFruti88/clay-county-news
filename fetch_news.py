import feedparser
import json

# Your news source
RSS_URL = "https://news.google.com/rss/search?q=Clay+County+IL+news"

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    news_items = []
    for entry in feed.entries[:10]:
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
            "source": entry.source.get('title', 'Local News')
        })
    with open("news.json", "w") as f:
        json.dump(news_items, f, indent=4)

if __name__ == "__main__":
    fetch_news()
