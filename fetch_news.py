import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def scrape_site_as_human(url):
    async with async_playwright() as p:
        # 1. Launch a real browser (Chromium)
        # headless=False allows you to watch it work; set to True for background tasks
        browser = await p.chromium.launch(headless=False)
        
        # 2. Create a browser context with a mobile/desktop persona
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )

        page = await context.new_page()

        # 3. Apply Stealth to hide "navigator.webdriver" and other bot flags
        await stealth_async(page)

        try:
            # 4. Navigate with a realistic timeout and "Referer"
            print(f"Navigating to {url}...")
            await page.goto(url, wait_until="networkidle")

            # 5. Mimic human behavior: Random scrolling
            # This triggers lazy-loading content and fools tracking scripts
            for _ in range(3):
                await page.mouse.wheel(0, random.randint(500, 1000))
                await asyncio.sleep(random.uniform(1, 3))

            # 6. Extract the source or specific data
            content = await page.content()
            title = await page.title()
            
            print(f"Successfully pulled data from: {title}")
            return content

        except Exception as e:
            print(f"Error encountered: {e}")
        
        finally:
            await browser.close()

# Example Usage
if __name__ == "__main__":
    target_url = "https://www.claycountynews.com/" # Replace with target
    html_source = asyncio.run(scrape_site_as_human(target_url))
    
    # Save the source to a file for inspection
    with open("source.html", "w", encoding="utf-8") as f:
        f.write(html_source)
