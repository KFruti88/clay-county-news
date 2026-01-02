import urllib.parse
import feedparser
import ssl
import json
import sys

def fetch_news():
    # 1. Define Sources
    # We add WNOI specifically as a direct source
    WNOI_RSS = "https://www.wnoi.com/category/local/feed"
    
    GOOGLE_BASE_URL = "https://news.google.com/rss/search?q="
    QUERY = '("Clay County IL" OR "Flora IL" OR "Louisville IL" OR "Clay City IL" OR "Effingham IL") when:7d'
    GOOGLE_RSS_URL = GOOGLE_BASE_URL + urllib.parse.quote(QUERY)

    # 2. SSL Fix for GitHub Actions/Server environments
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except Exception:
        pass

    articles = []
    seen_titles = set() # To prevent duplicate stories

    # User-Agent to prevent being blocked
    UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'

    # 3. Fetch from WNOI (Direct Local)
    print(f"Fetching from WNOI Local News...")
    wnoi_feed = feedparser.parse(WNOI_RSS, agent=UA)
    
    for entry in wnoi_feed.entries:
        clean_title = entry.title.split(' - ')[0].strip()
        if clean_title.lower() not in seen_titles:
            articles.append({
                "title": clean_title,
                "link": entry.link,
                "date": getattr(entry, 'published', 'Recently'),
                "source": "WNOI Radio"
            })
            seen_titles.add(clean_title.lower())

    # 4. Fetch from Google News (Broader Search)
    print(f"Searching Google News for surrounding areas...")
    google_feed = feedparser.parse(GOOGLE_RSS_URL, agent=UA)
    
    if google_feed.entries:
        for entry in google_feed.entries[:15]: # Take top 15 from Google
            clean_title = entry.title.split(' - ')[0].strip()
            # Only add if we haven't already seen this title from WNOI
            if clean_title.lower() not in seen_titles:
                articles.append({
                    "title": clean_title,
                    "link": entry.link,
                    "date": getattr(entry, 'published', 'Recently'),
                    "source": entry.source.title if hasattr(entry, 'source') else "Local News"
                })
                seen_titles.add(clean_title.lower())
    
    print(f"Total articles gathered: {len(articles)}")

    # 5. Save to JSON
    with open('news_data.json', 'w') as f:
        json.dump(articles, f, indent=4)
    print("Data saved to news_data.json")

if __name__ == "__main__":
    try:
        fetch_news()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
