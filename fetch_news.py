import asyncio
import json
import random
import os
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
DATA_EXPORT_FILE = "news_data.json"

# --- 2. CREDENTIALS ---
WP_USER = os.getenv("WP_USER", "your_username")
WP_APP_PASSWORD = os.getenv("WP_PWD", "your_app_password")

# --- 3. CORE FUNCTIONS ---

def load_history():
    """Loads previously posted links to avoid duplicates."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return []
    return []

def save_history(links):
    """Saves the last 500 posted links with formatting."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(links[-500:], f, indent=4)

async def post_to_wordpress(site_url, title, brief, full_news_link):
    """Pushes news to WordPress via REST API using httpx."""
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
            return response.status_code == 201
        except Exception as e:
            print(f"    [Error] WP Connection: {e}")
            return False

async def scrape_towns():
    """Main engine: Scrapes NewsBreak and distributes content."""
    all_results = {}
    history = load_history()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page)

        for town, url in TOWN_SOURCES.items():
            print(f"[*] Processing {town}...")
            town_stories = []
            
            try:
                await page.goto(url, wait_until="networkidle")
                await page.mouse.wheel(0, 800)
                await asyncio.sleep(random.uniform(2, 4))

                articles = await page.locator("article").all()
                processed_count = 0

                for article in articles:
                    if processed_count >= 3: 
                        break

                    try:
                        title_node = article.locator("h3")
                        if await title_node.count() == 0: continue
                        
                        title = await title_node.inner_text()
                        link_node = article.locator("a").first
                        href = await link_node.get_attribute("href")
                        if not href: continue
                            
                        full_link = href if href.startswith("http") else f"https://www.newsbreak.com{href}"

                        if full_link in history:
                            print(f"  - Skipping: {title[:40]}...")
                            continue

                        summary_node = article.locator("p, .description, .summary").first
                        raw_summary = await summary_node.inner_text() if await summary_node.count() > 0 else "Local news update."
                        brief = (raw_summary[:180] + "...") if len(raw_summary) > 180 else raw_summary

                        target_site = SITE_MAPPING.get(town, MAIN_HUB)
                        
                        # Distribution Step
                        posted = await post_to_wordpress(target_site, title, brief, full_link)

                        if posted:
                            if target_site != MAIN_HUB:
                                await post_to_wordpress(MAIN_HUB, title, brief, full_link)
                            
                            history.append(full_link)
                            town_stories.append({"title": title, "link": full_link})
                            processed_count += 1
                            print(f"    [OK] Distributed: {title[:40]}")

                    except Exception:
                        continue

                all_results[town] = town_stories
                await asyncio.sleep(random.uniform(3, 7))

            except Exception as e:
                print(f" [Critical] {town} failed: {e}")

        await browser.close()
    
    save_history(history)
    return all_results

# --- 4. EXECUTION ---
if __name__ == "__main__":
    print("Starting News Pipeline...")
    try:
        final_data = asyncio.run(scrape_towns())
        with open(DATA_EXPORT_FILE, "w") as f:
            json.dump(final_data, f, indent=4)
        print("Done. Exported to news_data.json")
    except Exception as e:
        print(f"Pipeline crashed: {e}")
