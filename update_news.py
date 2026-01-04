import requests
from bs4 import BeautifulSoup
import json
import os

# The local news URL you want to scrape
URL = "https://www.claytodayonline.com/" # Update this to your preferred local source

def scrape_news():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # This looks for common article patterns - adjust based on the specific site
    articles = soup.find_all('div', class_='art-content') # This class changes per site!
    
    new_stories = []
    
    # Load existing links to avoid duplicates
    if os.path.exists('posted_links.json'):
        with open('posted_links.json', 'r') as f:
            posted_links = json.load(f)
    else:
        posted_links = []

    for art in articles:
        title_element = art.find('h3')
        link_element = art.find('a')
        
        if title_element and link_element:
            title = title_element.text.strip()
            link = link_element['href']
            
            if link not in posted_links:
                new_stories.append({
                    "title": title,
                    "full_story": "Click original link for full details.", # Or scrape deeper
                    "tags": ["Clay County"],
                    "slug": title.lower().replace(" ", "-")[:50]
                })
                posted_links.append(link)

    # Save findings
    if new_stories:
        with open('news_data.json', 'w') as f:
            json.dump(new_stories, f, indent=4)
        with open('posted_links.json', 'w') as f:
            json.dump(posted_links, f, indent=4)
        print(f"Success: Added {len(new_stories)} new stories.")
    else:
        print("No new stories found.")

if __name__ == "__main__":
    scrape_news()
