import urllib.parse
import feedparser

def fetch_news():
    # 1. Define the base URL (Google News RSS is the most common for this query format)
    BASE_URL = "https://news.google.com/rss/search?q="
    
    # 2. Define your raw query with spaces and quotes
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

    # 3. URL Encode the query (this converts spaces to %20 and quotes to %22)
    # This prevents the "InvalidURL: URL can't contain control characters" error
    encoded_query = urllib.parse.quote(QUERY)
    RSS_URL = BASE_URL + encoded_query

    print(f"Fetching news from: {RSS_URL}")

    # 4. Parse the feed
    feed = feedparser.parse(RSS_URL)

    # 5. Check if the feed was parsed successfully
    if feed.bozo:
        print(f"Error parsing feed: {feed.bozo_exception}")
        return

    print(f"Found {len(feed.entries)} articles.\n")

    # 6. Loop through and print results
    for entry in feed.entries:
        print(f"Title: {entry.title}")
        print(f"Link:  {entry.link}")
        print(f"Published: {entry.published}")
        print("-" * 30)

if __name__ == "__main__":
    fetch_news()
