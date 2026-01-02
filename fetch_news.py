import urllib.parse
import feedparser
import ssl
import sys

def fetch_news():
    # 1. Setup Base URL and the search query
    BASE_URL = "https://news.google.com/rss/search?q="
    
    # We combine the locations into one clean string
    QUERY = (
        'site:newsbreak.com/louisville-il OR site:newsbreak.com/flora-il OR '
        'site:newsbreak.com/clay-city-il OR site:newsbreak.com/sailor-springs-il OR '
        'site:newsbreak.com/xenia-il OR site:newsbreak.com/iola-il OR '
        '"Clay County IL" OR "Effingham IL" OR "Fairfield IL" OR '
        '"Salem IL" OR "Mt. Vernon IL"'
    )

    # 2. URL Encoding - This fixes the 'control characters' crash
    encoded_query = urllib.parse.quote(QUERY)
    RSS_URL = BASE_URL + encoded_query

    # 3. Handle SSL/Security context for GitHub Actions
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except Exception:
        pass

    print(f"Checking for news in Clay County and surrounding areas...")
    print(f"URL: {RSS_URL}\n")

    # 4. Fetch the data using a browser-like User-Agent
    feed = feedparser.parse(RSS_URL, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsBot/1.0')

    # 5. Check for parsing errors
    if feed.bozo:
        print(f"ERROR: Could not read the news feed. Reason: {feed.bozo_exception}")
        return

    # 6. Check if entries are empty
    if not feed.entries:
        print("No news articles found. Try simplifying the search query if this continues.")
        return

    # 7. Display the results
    print(f"SUCCESS: Found {len(feed.entries)} articles.\n")
    
    for i, entry in enumerate(feed.entries[:15], 1):  # Shows top 15 results
        print(f"{i}. {entry.title}")
        print(f"   Link: {entry.link}")
        if hasattr(entry, 'published'):
            print(f"   Date: {entry.published}")
        print("-" * 50)

if __name__ == "__main__":
    try:
        fetch_news()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
