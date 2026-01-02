import urllib.parse
import feedparser
import ssl
import json
import sys

def fetch_news():
    # 1. We use a broader search query. 
    # Searching "site:newsbreak.com/flora-il" is too restrictive for RSS.
    # Searching "Flora IL News" works much better.
    BASE_URL = "https://news.google.com/rss/search?q="
    QUERY = (
        '("Clay County IL" OR "Flora IL" OR "Louisville IL" OR "Clay City IL" OR "Effingham IL") '
        'when:7d' # This tells Google to only get news from the last 7 days
    )

    encoded_query = urllib.parse.quote(QUERY)
    RSS_URL = BASE_URL + encoded_query

    # 2. SSL Fix
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except Exception:
        pass

    print(f"Searching for local news...")

    # 3. Use a more convincing User-Agent to avoid being blocked
    feed = feedparser.parse(RSS_URL, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')

    articles = []
    
    if feed.entries:
        for entry in feed.entries[:20]:
            # We clean up the title (Google News adds the source at the end like " - NewsBreak")
            clean_title = entry.title.split(' - ')[0]
            
            articles.append({
                "title": clean_title,
                "link": entry.link,
                "date": getattr(entry, 'published', 'Recently'),
                "source": entry.source.title if hasattr(entry, 'source') else "Local News"
            })
        print(f"Found {len(articles)} recent articles!")
    else:
        print("No articles found with current keywords. Trying fallback...")
        # Fallback to a very simple search if the complex one fails
        feed = feedparser.parse(BASE_URL + urllib.parse.quote("Clay County Illinois"), agent='Mozilla/5.0')
        # ... (process fallback entries similar to above)

    # 4. Save to JSON for your HTML page
    with open('news_data.json', 'w') as f:
        json.dump(articles, f, indent=4)

if __name__ == "__main__":
    fetch_news()
