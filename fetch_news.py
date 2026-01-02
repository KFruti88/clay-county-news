import urllib.parse
import feedparser
import ssl

def fetch_news():
    # 1. The Base URL for the RSS service (likely Google News based on your query)
    BASE_URL = "https://news.google.com/rss/search?q="
    
    # 2. Your specific search query
    QUERY = (
        'site:newsbreak.com/louisville-il OR '
        'site:newsbreak.com/flora-il OR '
        'site:newsbreak.com/clay-city-il OR '
        'site:newsbreak.com/sailor-springs-il OR '
        'site:newsbreak.com/xenia-il OR '
        'site:newsbreak.com/iola-il OR '
        '"Clay County IL" OR "Effingham IL" OR "Fairfield IL" OR '
        '"Salem IL" OR "Mt. Vernon IL"'
    )

    # 3. FIX: Encode the query to handle spaces and quotes
    # This turns "Clay County" into "Clay%20County"
    encoded_query = urllib.parse.quote(QUERY)
    RSS_URL = BASE_URL + encoded_query

    # 4. Fix for SSL certificate issues (common in GitHub Actions/Docker)
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context

    print(f"Connecting to: {RSS_URL}")

    # 5. Fetch the feed
    # We add an agent because some servers block the default python-urllib agent
    feed = feedparser.parse(RSS_URL, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

    # 6. Error Handling for the feed itself
    if not feed.entries:
        print("No news items found or the feed is unreachable.")
        return

    # 7. Process the results
    for entry in feed.entries:
        print(f"Title: {entry.title}")
        print(f"Link:  {entry.link}")
        print("-" * 20)

if __name__ == "__main__":
    try:
        fetch_news()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1) # Ensures the GitHub Action registers a failure if it crashes
