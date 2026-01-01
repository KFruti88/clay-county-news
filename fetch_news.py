import feedparser
import json
from datetime import datetime, timedelta
import time

# 1. THE STRICT FILTER LIST
# Any news from Effingham, Mt. Vernon, etc., MUST mention one of these to be saved.
CLAY_COUNTY_TOWNS = ['flora', 'clay city', 'louisville', 'sailor springs', 'xenia', 'iola', 'clay county']

# 2. THE BROAD SEARCH QUERY
# This tells Google News where to look.
SEARCH_QUERY = (
    "site:newsbreak.com/louisville-il OR site:newsbreak.com/flora-il OR "
    "site:newsbreak.com/clay-city-il OR site:newsbreak.com/sailor-springs-il OR "
    "site:newsbreak.com/xenia-il OR site:newsbreak.com/iola-il OR "
    "\"Clay County IL\" OR \"Effingham IL\" OR \"Fairfield IL\" OR "
    "\"Salem IL\" OR \"Mt. Vernon IL\""
)

RSS_URL = f"https://news.google.com/rss/search?q={SEARCH_QUERY}"

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    news_items = []
    
    # Looking back 7 days (168 hours) to ensure a full feed
    cutoff = datetime.now() - timedelta(hours=168)

    for entry in feed.entries:
        if not hasattr(entry, 'published_parsed'):
            continue
            
        published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        
        if published_dt > cutoff:
            title = entry.title
            summary = entry.summary if hasattr(entry, 'summary') else ""
            # We check both the title and summary for Clay County keywords
            content_to_check = (title + " " + summary).lower()

            # --- THE GATEKEEPER ---
            # This ensures only Clay County related news gets through
            if any(town in content_to_check for town in CLAY_COUNTY_TOWNS):
                
                source_name = entry.source.title if hasattr(entry, 'source') else "Local News"
                if "newsbreak" in source_name.lower():
                    source_name = "NewsBreak"

                news_items.append({
                    "title": title,
                    "link": entry.link,
                    "published_dt": published_dt.isoformat(),
                    "published": entry.published,
                    "source": source_name,
                    "summary": summary
                })
    
    # 3. DEDUPLICATE AND SORT
    seen_titles = set()
    unique_items = []
    for item in news_items:
        if item['title'] not in seen_titles:
            unique_items.append(item)
            seen_titles.add(item['title'])

    unique_items.sort(key=lambda x: x.get('published_dt', ''), reverse=True)
    
    # 4. SAVE TO JSON
    with open("news.json", "w") as f:
        json.dump(unique_items, f, indent=4)

if __name__ == "__main__":
    fetch_news()
