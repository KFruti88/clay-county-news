import asyncio
import random
import requests
import os
from requests.auth import HTTPBasicAuth
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- CONFIGURATION ---
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
    "Sailor Springs": "https://supportmylocalcommunity.com/sailor-springs/",
}

MAIN_HUB = "https://supportmylocalcommunity.com"

# --- CREDENTIALS ---
# Replace with your actual details or use GitHub Secrets (os.environ.get)
WP_USER = "your_username"
WP_APP_PASSWORD = "your_application_password"

# --- CORE FUNCTIONS ---

async def post_to_wordpress(site_url, title, link):
    """Sends the news to the specific WordPress REST API."""
    api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    content = f"Latest local news update. <br><br> <a href='{link}'>Read full story on NewsBreak</a>"
    
    payload = {"title": title, "content": content, "status": "publish"}
    
    try:
        response = requests.post(
            api_url,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            json=payload,
            timeout=10
        )
        if response.status_code == 201:
            print(f" [OK] Posted to {site_url}")
        else:
            print(f" [Error {response.status_code}] on {site_url}: {response.text}")
    except Exception as e:
        print(f" [Conn Error] {site_url}: {e}")

async def scrape_town_news(page, town_name, url):
    """Navigates to NewsBreak and pulls the titles and links."""
    print(f"\n--- Processing {town_name} ---")
    try:
        await page.goto(url, wait_until="networkidle")
        
        # Mimic human interaction
        await page.mouse.wheel(0, random.randint(500, 1000))
        await asyncio.sleep(random.uniform(3, 6))

        # Select all article blocks
        articles = await page.locator("article").all()
        
        processed_count = 0
        for article in articles:
            if processed_count >= 3: break # Limit to top 3 stories per town
            
            title_node = article.locator("h3")
            link_node = article.locator("a").first
            
            if await title_node.count() > 0:
                title = await title_node.inner_text()
                href = await link_node.get_attribute("href")
                
                # Ensure the link is a full URL
                link = href if href.startswith("http") else f"https://www.newsbreak.com{href}"

                print(f"Found: {title[:50]}...")
                
                # Determine destination
                target_site = SITE_MAPPING.get(town_name, MAIN_HUB)
                
                # Post to specific site and the main hub
                await post_to_wordpress(target_site, title, link)
                if target_site != MAIN_HUB:
                    await post_to_wordpress(MAIN_HUB, title, link)
                
                processed_count += 1
                
    except Exception as e:
        print(f"Failed to scrape {town_name}: {e}")

async def run_hub():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        await stealth_async(page)

        for town, url in TOWN_SOURCES.items():
            await scrape_town_news(page, town, url)
            await asyncio.sleep(random.uniform(5, 12)) # Human-like delay

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_hub())
