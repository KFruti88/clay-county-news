async def run():
    # Use a dictionary to stop duplicate titles.
    # Title is the 'Key', ensuring each story only exists once in the file.
    seen_stories = {} 

    print("Gathering news and deduplicating...")
    
    # 1. Process RSS (Regional News)
    regional = await fetch_rss()
    for story in regional:
        seen_stories[story['title']] = story

    # 2. Process Town Scrapes (Specific Local News)
    for town in TOWNS:
        print(f"Checking {town}...")
        town_stories = await scrape_town(town)
        for story in town_stories:
            title = story['title']
            if title in seen_stories:
                # Story exists! Update existing story with new town tag if not already there
                if town not in seen_stories[title]['tags']:
                    seen_stories[title]['tags'].append(town)
            else:
                # Brand new story found, add to dictionary
                seen_stories[title] = story

    # 3. Export to JSON (Flat List)
    final_list = list(seen_stories.values())
    with open(DATA_EXPORT_FILE, "w") as f:
        json.dump(final_list, f, indent=4)
        
    print(f"Update complete! Saved {len(final_list)} unique, tagged stories to {DATA_EXPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(run())
