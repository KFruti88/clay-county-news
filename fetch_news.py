import asyncio
import random
import requests
import json
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
    "Sailor Springs": "https://supportmylocalcommunity.com/louisville/", # Linked to Louisville
}

MAIN_HUB = "https://supportmylocalcommunity.com"

# --- 2. CREDENTIALS ---
# In WP Dashboard: Users > Profile > Application Passwords
WP_USER = "your_username"
WP_APP_PASSWORD = "your_app_password"

# --- 3. CORE FUNCTIONS ---

async def post_to_wordpress(site_url, title, brief, full_news_link):
    """Pushes a brief summary and 'Read More' link to WordPress sites."""
    api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    # The 'Read More' link points to the full article on NewsBreak
    content = f"{brief}<br><br><strong><a href='{full_news_link}'>Read Full Story &raquo;</a></strong>"
    
    payload = {
        "title": title,
        "content": content,
        "status": "publish"
    }
    
    try:
        response = requests.post(
            api_url,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            json=payload,
            timeout=10
        )
        if response.status_code == 201:
            print(f" [OK] Posted to {site_url}")
        return response.status_code == 201
    except Exception as e:
        print(f" [Error] WordPress post failed for {site_url}: {e}")
        return False

async def scrape_towns():
    """Main scraping engine."""
    all_news_data = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page)

        for town, url in TOWN_SOURCES.items():
            print(f"\n--- Scraping {town} ---")
            try:
                await page.goto(url, wait_until="networkidle")
                await page.mouse.wheel(0, 600)
                await asyncio.sleep(random.uniform(3, 6))

                articles = await page.locator("article").all()
                town_stories = []

                for article in articles[:3]: # Limit to top 3
                    # Get Title
                    title = await article.locator("h3").inner_text()
                    
                    # Get Link
                    link_node = article.locator("a").first
                    href = await link_node.get_attribute("href")
                    full_link = href if href.startswith("http") else f"https://www.newsbreak.com{href}"

                    # Get Brief Summary
                    summary_node = article.locator("p, .description, .summary").first
                    raw_summary = await summary_node.inner_text() if await summary_node.count() > 0 else "Local news update for the community."
                    brief = (raw_summary[:180] + "...") if len(raw_summary) > 180 else raw_summary

                    # Determine Destination
                    target_site = SITE_MAPPING.get(town, MAIN_HUB)
                    
                    # 1. Post to specific town site
                    await post_to_wordpress(target_site, title, brief, full_link)
                    
                    # 2. Post to the main hub
                    if target_site != MAIN_HUB:
                        await post_to_wordpress(MAIN_HUB, title, brief, full_link)

                    # Store for our GitHub index.html
                    town_stories.append({
                        "title": title,
                        "brief": brief,
                        "target_site": target_site # This links the "More" button to the town site
                    })

                all_news_data[town] = town_stories

            except Exception as e:
                print(f"Failed to scrape {town}: {e}")
            
            await asyncio.sleep(random.uniform(5, 10))

        await browser.close()
    return all_news_data

if __name__ == "__main__":
    # Run the scraper
    news_results = asyncio.run(scrape_towns())
    
    # Save the data for the index.html newspaper layout
    with open("news_data.json", "w") as f:
        json.dump(news_results, f, indent=4)
        
    print("\nMission Accomplished: All sites updated and data file generated.")
