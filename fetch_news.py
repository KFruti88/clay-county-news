async def scrape_towns():
    """Main engine: Scrapes NewsBreak and distributes content."""
    all_results = {}
    history = load_history()

    async with async_playwright() as p:
        # Launch browser - headless=True for production use
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
                
                # Human-like interaction to trigger dynamic content
                await page.mouse.wheel(0, 800)
                await asyncio.sleep(random.uniform(2, 4))

                articles = await page.locator("article").all()
                processed_count = 0

                for article in articles:
                    # Limit to top 3 NEW stories per town
                    if processed_count >= 3: 
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

                        # Duplicate Check
                        if full_link in history:
                            print(f"  - Skipping: {title[:50]}...")
                            continue

                        # Extract Summary
                        summary_node = article.locator("p, .description, .summary").first
                        raw_summary = await summary_node.inner_text() if await summary_node.count() > 0 else "Latest community update."
                        brief = (raw_summary[:180] + "...") if len(raw_summary) > 180 else raw_summary

                        # Distribution Logic
                        target_site = SITE_MAPPING.get(town, MAIN_HUB)
                        
                        # Step 1: Post to Town Site
                        success = await post_to_wordpress(target_site, title, brief, full_link)

                        # Step 2: Mirror to Main Hub if successful
                        if success:
                            if target_site != MAIN_HUB:
                                await post_to_wordpress(MAIN_HUB, title, brief, full_link)
                            
                            # Update local history and results tracking
                            history.append(full_link)
                            town_stories.append({
                                "title": title, 
                                "brief": brief, 
                                "link": full_link,
                                "target_site": target_site
                            })
                            processed_count += 1

                    except Exception as e:
                        print(f"  [Error] Article skip: {e}")
                        continue

                all_results[town] = town_stories
                
                # Anti-bot delay between towns
                await asyncio.sleep(random.uniform(5, 10))

            except Exception as e:
                print(f"  [Critical] Failed {town}: {e}")

        await browser.close()
    
    # Save the updated history for the next run
    save_history(history)
    return all_results
