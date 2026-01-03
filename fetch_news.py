import asyncio
import random
import os
import json
import httpx
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- 1. CONFIGURATION ---
SITE_MAPPING = {
    "Flora": "https://ourflora.com",
    "Clay City": "https://supportmylocalcommunity.com/clay-city/",
    "Xenia": "https://supportmylocalcommunity.com/xenia/",
    "Louisville": "https://supportmylocalcommunity.com/louisville/",
    "Sailor Springs": "https://supportmylocalcommunity.com/louisville/",
}

TOWN_SOURCES = {
    "Flora": "https://www.newsbreak.com/flora-il",
    "Clay City": "https://www.newsbreak.com/clay-city-il",
    "Xenia": "https://www.newsbreak.com/xenia-il",
    "Louisville": "https://www.newsbreak.com/louisville-il",
    "Sailor Springs": "https://www.newsbreak.com/sailor-springs-il"
}

MAIN_HUB = "https://supportmylocalcommunity.com"
HISTORY_FILE = "posted_links.json"

# --- 2. CREDENTIALS ---
# It is best to set these as Environment Variables on your system
WP_USER = os.getenv("WP_USER", "your_username")
WP_APP_PASSWORD = os.getenv("WP_PWD", "your_app_password")

# --- 3. CORE FUNCTIONS ---

def load_history():
    """Loads previously posted links to avoid duplicates."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(links):
    """Saves the last 500 posted links with formatting."""
    with open(HISTORY_FILE, "w") as f:
        # indent=4 makes the file human-readable for debugging
        json.dump(links[-500:], f, indent=4)

async def post_to_wordpress(site_url, title, brief, full_news_link):
    """Pushes news to WordPress via REST API using non-blocking httpx."""
    api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    content = (
        f"{brief}<br><br>"
        f"<strong><a href='{full_news_link}' target='_blank' rel='noopener'>"
        f"Read Full Story &raquo;</a></strong>"
    )
    
    payload = {"title": title, "content": content, "status": "publish"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                api_url,
                auth=(WP_USER, WP_APP_PASSWORD),
                json=payload,
                timeout=20
            )
            if response.status_code == 201:
                print(f"    [OK] Posted to {site_url}")
                return True
            print(f"    [Fail] {site_url} status: {response.status_code}")
        except Exception as e:
            print(f"    [Error] Connection failed for {site_url}: {e}")
    return False

async def scrape_towns():
    """Main engine: Scrapes NewsBreak and distributes content."""
    all_news_data = {}
    history = load_history()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page)

        for town, url in TOWN_SOURCES.items():
            print(f"\n--- Processing {town} ---")
            town_stories = []
            
            try:
                await page.goto(url, wait_until="networkidle")
                await page.mouse.wheel(0, 800)
                await asyncio.sleep(random.uniform(2, 4))
                
                articles = await page.locator("article").all()
                count = 0

                for article in articles:
                    if count >= 3: break 
                    
                    try:
                        title = await article.locator("h3").inner_text()
                        link_node = article.locator("a").first
                        href = await link_node.get_attribute("href")
                        full_link = href if href.startswith("http") else f"https://www.newsbreak.com{href}"

                        # Skip if story was already processed
                        if full_link in history:
                            continue

                        summary_node = article.locator("p, .description, .summary").first
                        raw_summary = await summary_node.inner_text() if await summary_node.count() > 0 else "Latest community update."
                        brief = (raw_summary[:180] + "...") if len(raw_summary) > 180 else raw_summary

                        target_site = SITE_MAPPING.get(town, MAIN_HUB)

                        # Distribution Logic
                        success = await post_to_wordpress(target_site, title, brief, full_link)
                        if success and target_site != MAIN_HUB:
                            await post_to_wordpress(MAIN_HUB, title, brief, full_link)

                        if success:
                            history.append(full_link)
                            town_stories.append({"title": title, "brief": brief, "target_site": target_site})
                            count += 1

                    except Exception:
                        continue 

                all_news_data[town] = town_stories

            except Exception as e:
                print(f"  [Critical] Failed to scrape {town}: {e}")

            await asyncio.sleep(random.uniform(5, 10)) # Anti-bot delay

        await browser.close()
    
    save_history(history)
    return all_news_data

if __name__ == "__main__":
    print("Starting News Distribution Pipeline...")
    results = asyncio.run(scrape_towns())
    
    # Export for frontend index.html newspaper layout
    with open("news_data.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("\nMission Accomplished: All sites updated and news_data.json sync'd.")
