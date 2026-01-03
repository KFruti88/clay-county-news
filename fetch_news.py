import asyncio
import json
import random
import os
import httpx
from playwright.async_api import async_playwright

# Resilient import for Playwright Stealth
try:
    from playwright_stealth import stealth_async
except ImportError:
    from playwright_stealth import stealth_page_async as stealth_async

# --- CONFIGURATION ---
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

WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_PWD")

# --- HELPERS ---
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except: return []
    return []

def save_history(links):
    with open(HISTORY_FILE, "w") as f:
        json.dump(links[-500:], f, indent=4)

async def post_to_wordpress(site_url, title, brief, full_news_link):
    if not WP_USER or not WP_APP_PASSWORD:
        print(f"!!! Credentials missing for {site_url}")
        return False
    
    api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    content = f"{brief}<br><br><strong><a href='{full_news_link}' target='_blank'>Read Full Story &raquo;</a></strong>"
    payload = {"title": title, "content": content, "status": "publish"}
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(api_url, auth=(WP_USER, WP_APP_PASSWORD), json=payload, timeout=25)
            return r.status_code == 201
        except Exception as e:
            print(f"Error posting: {e}")
            return False

# --- ENGINE ---
async def run_pipeline():
    history = load_history()
    all_results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Apply stealth using the resilient import
        await stealth_async(page)

        for town, url in TOWN_SOURCES.items():
            print(f"[*] Checking {town}...")
            town_stories = []
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.mouse.wheel(0, 500)
                await asyncio.sleep(random.uniform(2, 4))
                
                articles = await page.locator("article").all()
                processed = 0
                for article in articles:
                    if processed >= 3: break
                    
                    h3 = article.locator("h3")
                    if await h3.count() == 0: continue
                    title = await h3.inner_text()
                    
                    link_node = article.locator("a").first
                    href = await link_node.get_attribute("href")
                    if not href: continue
                    full_link = href if href.startswith("http") else f"https://www.newsbreak.com{href}"

                    if full_link in history: continue

                    summary_node = article.locator("p, .description, .summary").first
                    raw_text = await summary_node.inner_text() if await summary_node.count() > 0 else "Local update."
                    brief = (raw_text[:180] + "...") if len(raw_text) > 180 else raw_text

                    target = SITE_MAPPING.get(town, MAIN_HUB)
                    if await post_to_wordpress(target, title, brief, full_link):
                        if target != MAIN_HUB:
                            await post_to_wordpress(MAIN_HUB, title, brief, full_link)
                        history.append(full_link)
                        town_stories.append({"title": title, "link": full_link})
                        processed += 1
                        print(f"    [OK] Posted: {title[:50]}...")

                all_results[town] = town_stories
                await asyncio.sleep(random.uniform(2, 5))
            except Exception as e:
                print(f" [!] {town} failed: {e}")

        await browser.close()
        save_history(history)
        with open(DATA_EXPORT_FILE, "w") as f:
            json.dump(all_results, f, indent=4)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
