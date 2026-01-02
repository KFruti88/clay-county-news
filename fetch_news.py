import urllib.parse
import feedparser
import ssl
import sys

def fetch_news():
    # 1. Setup Base URL and Query
    BASE_URL = "https://news.google.com/rss/search?q="
    QUERY = (
        'site:newsbreak.com/louisville-il OR '
        'site:newsbreak.com/flora-il OR '
        '"Clay County IL" OR "Effingham IL"'
    )

    # 2. URL Encoding (Fixes your specific crash)
    encoded_query = urllib.parse.quote(QUERY)
    RSS_URL = BASE_URL + encoded_query

    # 3. Handle SSL/Security (Prevents "loading" forever or SSL errors)
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except AttributeError:
        pass

    print(f"--- Starting News Fetch ---")
    print(f"Target URL: {RSS_URL}\n")

    # 4. Fetch the data with a User-Agent (Prevents being blocked)
    # If the script stays "blank," it's usually because the server is ignoring the request.
    feed = feedparser.parse(RSS_URL, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsBot/1.0')

    # 5. Output Results or Detailed Errors
    if feed.bozo:
        print(f"CRITICAL ERROR: The feed could not be parsed.")
        print(f"Reason: {feed.bozo_exception}")
        return

    if not feed.entries:
        print("!!! WARNING: Connection successful, but NO ARTICLES were found.")
        print("Try simplifying your QUERY string.")
        return

    # 6. Display the News
    print(f"SUCCESS: Found {len(feed.entries)} articles.\n")
    
    for i, entry in enumerate(feed.entries[:10], 1):  # Show top 10
        print(f"{i}. {entry.title}")
        print(f"   Link: {entry.link}")
        print(f"   Date: {entry.published}")
        print("-" * 40)

if __name__ == "__main__":
    try:
        fetch_news()
    except Exception as e:
        print(f"APPLICATION CRASHED: {str(e)}")
        sys.exit(1)
