import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

# --- SETTINGS ---
JSON_FILE = "news_data.json"

def generate_slug(title):
    """
    Creates a URL-friendly 'bookmark'. 
    Example: 'Police & Fire News!' becomes 'police-fire-news'
    """
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug) # Remove special characters
    slug = re.sub(r'[\s_-]+', '-', slug) # Replace spaces with dashes
    return slug

def scrape_news():
    # ... (your scraping logic here) ...
    all_news = []
    
    # Example of how to structure the dictionary inside your loop:
    # for article in articles:
    #    title = article.find('h2').text
    #    story_text = article.find('p').text
    
    news_entry = {
        "title": title,
        "slug": generate_slug(title),  # <--- THIS IS THE KEY FOR THE BOOKMARK
        "full_story": story_text,
        "tags": ["Flora"], # Example tag
        "date_added": datetime.now().isoformat()
    }
    all_news.append(news_entry)
    return all_news

# ... (rest of your saving logic) ...
