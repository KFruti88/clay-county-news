import asyncio
import random
import os
import json
import httpx  # Better for async than 'requests'
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- 1. CONFIGURATION ---
SITE_MAPPING = {
    "Clay City": "https://supportmylocalcommunity.com/clay-city/",
    "Xenia": "https://supportmylocalcommunity.com/xenia/",
    "Louisville": "https://supportmylocalcommunity.com/louisville/",
    "Sailor Springs": "https://supportmylocalcommunity.com/louisville/", 
}

TOWN_SOURCES = {
    "Clay City": "https://www.newsbreak.com/clay-city-il",
    "Xenia": "https://www.newsbreak.com/xenia-il",
    "Louisville": "https://www.newsbreak.com/louisville-il",
    "Sailor Springs": "https://www.newsbreak.com/sailor-springs-il"
}

MAIN_HUB = "https://supportmylocalcommunity.com"
WP_USER = "your_username"
WP_APP_PASSWORD = "your_app_password" # Generated in WP > Users > Profile
HISTORY_FILE = "posted_links.json"

# --- 2. CORE FUNCTIONS ---

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(links):
    with open(HISTORY_FILE, "w") as f:
        json.dump(links[-500:], f) # Keep last 500 links

async def post_to_wordpress(site_url, title, brief, full_news_link):
    """Pushes a brief summary and 'Read More' link to WordPress sites via REST API."""
    api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    content = f"{brief}<br><br><strong><a href='{full_news_link}'>Read Full Story &raquo;</a></strong>"
    payload = {
        "title": title,
        "content": content,
        "status": "publish"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                api_url,
                auth=(WP_USER, WP_APP_PASSWORD),
                json=payload,
                timeout=20
            )
            if response.status_code == 201:
                print(f"  [OK] Posted to {site_url}")
                return True
            else:
                print(f"  [Fail] {site_url} returned {response.status_code}")
        except Exception as e:
            print(f"  [Error] WordPress API error for {site_url}: {e}")
    return False

async def scrape_towns():
    """Main scraping engine using Playwright Stealth."""
    all_news_data = {}
    history = load_history()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 ...")
        page = await context.new_page()
        await stealth_async(page)

        for town, url in TOWN_SOURCES.items():
            print(f"\n--- Scraping {town} ---")
            try:
                await page.goto(url, wait_until="networkidle")
                await page.mouse.wheel(0, 1000) # Scroll to trigger lazy loading
                await asyncio.sleep(2)

                articles = await page.locator("article").all()
                town_stories = []

                for article in articles[:3]: # Limit to top 3 fresh stories
                    try:
                        title = await article.locator("h3").inner_text()
                        
                        # Handle Link Extraction
                        link_node = article.locator("a").first
                        href = await link_node.get_attribute("href")
                        full_link = href if href.startswith("http") else f"https://www.newsbreak.com{href}"

                        # Skip if already posted
                        if full_link in history:
                            continue

                        # Extract Summary
                        summary_node = article.locator("p, .description, .summary").first
                        raw_summary = await summary_node.inner_text() if await summary_node.count() > 0 else "Local news update for the community."
                        brief = (raw_summary[:180] + "...") if len(raw_summary) > 180 else raw_summary

                        target_site = SITE_MAPPING.get(town, MAIN_HUB)

                        # Post to specific town site
                        success = await post_to_wordpress(target_site, title, brief, full_link)
                        
                        # Post to the main hub
                        if success and target_site != MAIN_HUB:
                            await post_to_wordpress(MAIN_HUB, title, brief, full_link)

                        if success:
                            history.append(full_link)
                            town_stories.append({
                                "title": title,
                                "brief": brief,
                                "target_site": target_site
                            })

                    except Exception as inner_e:
                        continue # Skip individual article if it fails

                all_news_data[town] = town_stories

            except Exception as e:
                print(f"Failed to scrape {town}: {e}")

            await asyncio.sleep(random.uniform(5, 10)) # Anti-bot delay

        await browser.close()
    
    save_history(history)
    return all_news_data

if __name__ == "__main__":
    print("Starting News Distribution Pipeline...")
    news_results = asyncio.run(scrape_towns())
    
    # Save for local newspaper dashboard
    with open("news_data.json", "w") as f:
        json.dump(news_results, f, indent=4)
        
    print("\nMission Accomplished: All sites updated and news_data.json generated.")
