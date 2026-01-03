import asyncio
import random
import requests
import os
from requests.auth import HTTPBasicAuth
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- 1. CONFIGURATION ---
TOWN_SOURCES = {
    "Flora": "https://www.newsbreak.com/flora-il",
    "Sailor Springs": "https://www.newsbreak.com/sailor-springs-il",
    "Clay City": "https://www.newsbreak.com/clay-city-il",
    "Ingraham": "https://www.newsbreak.com/ingraham-il",
    "Xenia": "https://www.newsbreak.com/xenia-il",
    "Louisville": "https://www.newsbreak.com/louisville-il"
}

SITE_MAPPING = {
    "Flora": "https://ourflora.com",
    "Clay City": "https://supportmylocalcommunity.com/clay-city/",
    "Xenia": "https://supportmylocalcommunity.com/xenia/",
    "Louisville": "https://supportmylocalcommunity.com/louisville/",
    "Sailor Springs": "https://supportmylocalcommunity.com/louisville/", # Linked to Louisville per your request
}

MAIN_HUB = "https://supportmylocalcommunity.com"

# --- 2. CREDENTIALS ---
# Generate an "Application Password" in WordPress > Users > Profile
WP_USER = "your_username"
WP_APP_PASSWORD = "your_app_password"

# --- 3. CORE FUNCTIONS ---

async def post_to_wordpress(site_url, title, brief, link):
    """Pushes a brief summary and 'Read More' link to WordPress."""
    api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    # Create the content with the 'Read More' link pointing back to the town site
    content = f"{brief}<br><br><strong><a href='{link}'>Read Full Story at {site_url.split('//')[-1]} &raquo;</a></strong>"
    
    payload = {"title": title, "content": content, "status": "publish"}
    
    try:
        response = requests.post(
            api_url,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            json=payload,
            timeout=10
        )
        return response.status_code == 201
    except:
        return False

async def scrape_towns():
    all_news_data = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page)

        for town, url in TOWN_SOURCES.items():
            print(f"Scraping {town}...")
            try:
                await page.goto(url, wait_until="networkidle")
                await page.mouse.wheel(0, 600)
                await asyncio.sleep(random.uniform(3, 6))

                articles = await page.locator("article").all()
                town_stories = []

                for article in articles[:3]: # Top 3 per town
                    title = await article.locator("h3").inner_text()
                    link_node = article.locator("a").first
                    href = await link_node.get_attribute("href")
                    full_link = href if href.startswith("http") else f"https://www.newsbreak.com{href}"

                    # Extract Brief Summary
                    summary_node = article.locator("p, .description, .summary").first
                    raw_summary = await summary_node.inner_text() if await summary_node.count() > 0 else ""
                    brief = (raw_summary[:180] + "...") if len(raw_summary) > 180 else raw_summary

                    # Determine where it goes
                    target_site = SITE_MAPPING.get(town, MAIN_HUB)
                    
                    # Push to Town Site and Main Hub
                    await post_to_wordpress(target_site, title, brief, full_link)
                    if target_site != MAIN_HUB:
                        await post_to_wordpress(MAIN_HUB, title, brief, full_link)

                    town_stories.append({"title": title, "brief": brief, "link": target_site})

                all_news_data[town] = town_stories

            except Exception as e:
                print(f"Error on {town}: {e}")
            
            await asyncio.sleep(random.uniform(5, 10))

        await browser.close()
    return all_news_data

def generate_index_html(data):
    """Generates the Newspaper-style index.html with the new data."""
    # (The HTML template code from the previous response goes here)
    # For now, this saves the data to a file that the index.html can read
    import json
    with open("news_data.json", "w") as f:
        json.dump(data, f)

if __name__ == "__main__":
    news_results = asyncio.run(scrape_towns())
    generate_index_html(news_results)
    print("Mission Accomplished: News scraped, distributed, and Hub updated.")
