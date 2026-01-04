def get_metadata(text):
    """Detects Category and tags either a specific Town OR County News."""
    category = "General News"
    icon = ""
    
    # 1. Detect Category
    if re.search(r'(?i)\bobituary\b|\bobituaries\b|\bpassed\s*away\b|\bdeath\s*notice\b', text):
        category = "Obituary"; icon = "🕊️ "
    elif re.search(r'(?i)\bfire\b|\brescue\b|\bextrication\b|\bstructure\s*fire\b|\bmutual\s*aid\b', text):
        category = "Fire & Rescue"; icon = "🚒 "
    elif re.search(r'(?i)\barrest\b|\bsheriff\b|\bpolice\b|\bbooking\b|\bcourt\s*news\b|\bblotter\b', text):
        category = "Police Report"; icon = "🚨 "

    # 2. Town Detection
    town_tags = []
    town_map = {
        "Flora": r'(?i)\bflora\b',
        "Xenia": r'(?i)\bxenia\b',
        "Louisville": r'(?i)\blouisville\b',
        "Clay City": r'(?i)clay\s*city',
        "Sailor Springs": r'(?i)sailor\s*springs'
    }
    
    for town, pattern in town_map.items():
        if re.search(pattern, text):
            town_tags.append(town)
    
    # If no town is mentioned, it's global "County News"
    if not town_tags:
        town_tags.append("County News")
            
    return category, town_tags, icon
