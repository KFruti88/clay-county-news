<div id="newspaper-container">
    <div class="newspaper-header">
        <h1 id="town-banner">Clay County News Center</h1>
        <div class="newspaper-meta">
            <span id="current-date"></span>
            <span id="chicago-time"></span>
            <span id="town-location">Flora Edition</span>
        </div>
    </div>
    <div id="news-grid">Loading headlines...</div>
</div>

<style>
    #newspaper-container { padding: 30px; border-radius: 12px; font-family: 'Times New Roman', serif; background: #fff; color: #000; box-shadow: 0 10px 40px rgba(0,0,0,0.1); max-width: 1000px; margin: auto; }
    .newspaper-meta { border-top: 2px solid #000; border-bottom: 5px solid #000; padding: 10px 0; display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 25px; }
    .article { padding: 30px; border-radius: 8px; margin-bottom: 30px; border-left: 12px solid #ccc; background: #f9f9f9; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .article h3 { font-size: 2rem; text-transform: uppercase; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
    .town-badge { display: inline-block; background: #333; color: #fff; padding: 4px 12px; border-radius: 4px; font-size: 0.9rem; font-weight: bold; margin-bottom: 10px; }
    .story-body { font-size: 1.15rem; line-height: 1.6; color: #333; }
    .border-flora { border-left-color: #ff5f05; }
    .border-louisville { border-left-color: #cc0000; }
</style>

<script>
(async () => {
    const MY_TOWN = "Flora"; // Change this for Louisville, etc.
    const DATA_URL = "https://raw.githubusercontent.com/KFruti88/clay-county-news/main/news_data.json";
    
    document.getElementById('current-date').innerText = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    try {
        const res = await fetch(DATA_URL);
        const data = await res.json();
        
        // FILTER: Keep only Flora news OR County-Wide news
        const filtered = data.filter(s => s.tags.includes(MY_TOWN) || s.tags.includes("County News"));
        
        const grid = document.getElementById('news-grid');
        grid.innerHTML = filtered.length ? "" : "No news for this region today.";

        filtered.forEach(story => {
            const colorClass = story.tags[0].toLowerCase().includes('flora') ? 'flora' : (story.tags[0].toLowerCase().includes('louisville') ? 'louisville' : 'general');
            grid.innerHTML += `
                <div class="article border-${colorClass}">
                    <span class="town-badge">${story.tags[0].toUpperCase()} EDITION</span>
                    <h3>${story.title}</h3>
                    <div class="story-body">
                        <strong>[${story.category}]</strong><br>
                        ${story.description}
                    </div>
                </div>`;
        });
    } catch (e) { console.error("Load failed:", e); }
})();
</script>
