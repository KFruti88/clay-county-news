import asyncio
import random
import requests
from requests.auth import HTTPBasicAuth
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- CONFIGURATION ---
# The NewsBreak URLs you want to monitor
TOWN_SOURCES = {
    "Flora": "https://www.newsbreak.com/flora-il",
    "Sailor Springs": "https://www.newsbreak.com/sailor-springs-il",
    "Clay City": "https://www.newsbreak.com/clay-city-il",
    "Ingraham": "https://www.newsbreak.com/ingraham-il",
    "Xenia": "https://www.newsbreak.com/xenia-il",
    "Louisville": "https://www.newsbreak.com/louisville-il"
}

# Where the news should be sent
SITE_MAPPING = {
    "Flora": "https://ourflora.com",
    "Clay City": "https://supportmylocalcommunity.com/clay-city/",
    "Xenia": "https://supportmylocalcommunity.com/xenia/",
    "Louisville": "https://supportmylocalcommunity.com/louisville/",
    "Sailor Springs": "https://supportmylocalcommunity.com/sailor-springs/",
}

MAIN_HUB = "https://supportmylocalcommunity.com"

# Your WordPress Credentials (Best used as Environment Variables)
WP_USER = "your_username"
WP_APP_PASSWORD = "your_application_password"

# --- FUNCTIONS ---

async def post_to_wordpress(site_url, title, link):
    """Sends the scraped news to the WordPress REST API."""
    api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    # Simple content body with a link to the original story
    content = f"Latest local news update. <br><br> <a href='{link}'>Read the full story on NewsBreak</a>"
    
    payload = {
        "title": title,
        "content": content,
        "status": "publish"
    }
    
    try:
        response = requests.post(
            api_url,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            json=payload
        )
        if response.status_code == 201:
            print(f"Successfully posted to {site_url}")
        else:
            print(f"Failed to post to {site_url}: {response.status_code}")
    except Exception as e:
        print(f"Connection error to {site_url}: {e}")

async def scrape_town_news(page, town_name, url):
    """Scrapes a specific NewsBreak town page."""
    print(f"Scraping {town_name}...")
    await page.goto(url, wait_until="networkidle")
    
    # Mimic human scrolling
    await page.mouse.wheel(0, random.randint(400, 800))
    await asyncio.sleep(random.uniform(2, 5))

    # Select articles (NewsBreak structure can change, usually looks for 'article' tags)
    articles = await page.locator("article").all()
    
    count = 0
    for article in articles:
        if count >= 3: break # Limit to top 3 articles per town to avoid spam
        
        try:
            # Extract title and link
            title_element = article.locator("h3")
            link_element = article.locator("a").first
            
            title = await title_element.inner_text()
            link = await link_element.get_attribute("href")

            if title and link:
                # 1. Post to the specific town site
                target_site = SITE_MAPPING.get(town_name, MAIN_HUB)
                await post_to_wordpress(target_site, title, link)
                
                # 2. ALSO post to the main hub
                if target_site != MAIN_HUB:
                    await post_to_wordpress(MAIN_HUB, title, link)
                
                count += 1
        except Exception:
            continue

async def main():
    async with async_playwright() as p:
        # Launch Stealth Browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page)

        # Loop through all towns
        for town, url in TOWN_SOURCES.items():
            await scrape_town_news(page, town, url)
            # Short rest between towns to look human
            await asyncio.sleep(random.uniform(5, 10))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
