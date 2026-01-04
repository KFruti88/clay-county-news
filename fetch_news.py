import re
import json
import xml.etree.ElementTree as ET

# Configuration
DATA_EXPORT_FILE = "calendar_events.json"

def clean_text(text):
    """Scrub branding, frequencies, and HTML tags based on your logic."""
    if not text: return ""
    
    # Patterns to remove (Fixed syntax from your snippet)
    patterns = [
        r'(?i)wnoi', 
        r'(?i)103\.9/99\.3', 
        r'(?i)local\s*--',
        r'(?i)by\s+tom\s+lavine', 
        r'^\d{1,2}/\d{1,2}/\d{2,4}\s*'
    ]
    
    for p in patterns:
        text = re.sub(p, '', text)
        
    # Remove HTML tags and extra whitespace
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def format_for_calendar(stories):
    """Converts scraped stories into FullCalendar-ready JSON."""
    calendar_events = []
    for story in stories:
        calendar_events.append({
            "title": story['title'],
            "start": story['date'], # Ensure your scraper provides ISO date (YYYY-MM-DD)
            "description": clean_text(story['full_text']),
            "url": story.get('link', ''),
            "extendedProps": {
                "town": story.get('town_tag', 'General')
            }
        })
    return calendar_events

# ... (Insert your RSS fetching logic here) ...

# Save the clean, de-duplicated list to the JSON file
# with open(DATA_EXPORT_FILE, "w") as f:
#     json.dump(final_output, f, indent=4)
