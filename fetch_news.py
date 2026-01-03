import asyncio
import json
import random
import os
from playwright.async_api import async_playwright

# Configuration
HISTORY_FILE = "history.json"
DATA_EXPORT_FILE = "news_data.json"
TOWNS = ["san-francisco-ca", "austin-tx", "new-york-ny"]  # Example slugs
BASE_URL = "https://www.newsbreak.com/"

# 1. History Management
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(links):
    """Saves the last 500 posted links with formatting."""
    with open(HISTORY_FILE, "w") as f:
        # Keep only the most recent 500 to keep file size small
        json.dump(links[-500:], f, indent=4)

# 2. WordPress Integration (Placeholder)
async def post_to_wordpress(site_url, title, brief, full_news_link):
    """
    Logic to post to WordPress REST API would go here.
    """
    print(f" [WP] Posting: {title}")
    # Example: requests.post(url, auth=auth, json=data)
    await asyncio.sleep(1) 
    return True

# 3. Main Scraper Logic
async def scrape_towns():
    history = load_history()
    results = []

    async with async_playwright() as p:
        # Launch browser (headless=True for production)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for town in TOWNS:
            url = f"{BASE_URL}{town}"
            print(f"[*] Scraping {town}...")
            
            try:
                await page.goto(url, wait_until="networkidle")
                
                # Human-like interaction
                await page.mouse.wheel(0, 800)
                await asyncio.sleep(random.uniform(2, 4))
                
                articles = await page.locator("article").all()
                count = 0
                
                for article in articles:
                    if count >= 3: # Limit to top 3 NEW stories per town
                        break
                    
                    try:
                        title_node = article.locator("h3")
                        if await title_node.count() == 0:
                            continue
                            
                        title = await title_node.inner_text()
                        link_node = article.locator("a").first
                        href = await link_node.get_attribute("href")
                        
                        if not href:
                            continue
                            
                        full_link = href if href.startswith("http") else f"https://www.newsbreak.com{href}"

                        # Duplicate check
                        if full_link in history:
                            print(f"  - Skipping (already processed): {title[:50]}...")
                            continue

                        # Add to results and history
                        news_item = {
                            "town": town,
                            "title": title,
                            "link": full_link
                        }
                        
                        # Simulate WordPress posting
                        success = await post_to_wordpress("mysite.com", title, "Summary here", full_link)
                        
                        if success:
                            results.append(news_item)
                            history.append(full_link)
                            count += 1

                    except Exception as article_err:
                        print(f"  [Error] Processing article: {article_err}")
                
                # Anti-bot delay between towns
                await asyncio.sleep(random.uniform(5, 10))

            except Exception as e:
                print(f" [Critical] Failed to scrape {town}: {e}")

        await browser.close()
        
    # Final cleanup: Save history and export data
    save_history(history)
    return results

# 4. Execution Entry Point
if __name__ == "__main__":
    print("Starting News Distribution Pipeline...")
    
    # Run the async scraper
    scraped_data = asyncio.run(scrape_towns())
    
    # Export for frontend newspaper layout
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(scraped_data, f, indent=4)
        
    print(f"\nPipeline Complete. {len(scraped_data)} new stories processed.")
