# Iterate through found articles
for article in articles:
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
            
        # Ensure the link is an absolute URL
        full_link = href if href.startswith("http") else f"https://www.newsbreak.com{href}"

        # Duplicate Check: Skip if we've handled this link in a previous run
        if full_link in history:
            print(f"  - Skipping: {title[:50]}...")
            continue

        # Extract and truncate summary for the brief
        summary_node = article.locator("p, .description, .summary").first
        raw_summary = await summary_node.inner_text() if await summary_node.count() > 0 else "Latest community update."
        brief = (raw_summary[:180] + "...") if len(raw_summary) > 180 else raw_summary

        # Distribution Logic
        target_site = SITE_MAPPING.get(town, MAIN_HUB)

        # Step 1: Post to the specific Town Site
        success = await post_to_wordpress(target_site, title, brief, full_link)

        # Step 2: Mirror to Main Hub if successful and the hub isn't already the target
        if success:
            if target_site != MAIN_HUB:
                await post_to_wordpress(MAIN_HUB, title, brief, full_link)
            
            # Update local tracking
            history.append(full_link)
            town_stories.append({
                "title": title, 
                "brief": brief, 
                "link": full_link,
                "target_site": target_site
            })
            processed_count += 1

    except Exception as e:
        print(f"  [Error] Failed to process article: {e}")
        continue
