document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    const processedIds = new Set();

    // 1. CONFIGURATION
    const jsonUrl = "https://kfruti88.github.io/clay-county-news/news_data.json";
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // 2. DETECT LOCATION
    const path = window.location.pathname.toLowerCase();
    const urlParams = new URLSearchParams(window.location.search);
    
    // Check if we are on the Full Article page or a Town page
    const isFullArticlePage = path.includes('local-news');
    const targetArticleId = urlParams.get('id');

    // Auto-detect town from the URL (e.g., /flora/ or /clay-city/)
    let currentTown = "";
    if (path.includes('flora')) currentTown = "Flora";
    else if (path.includes('clay-city')) currentTown = "Clay City";
    else if (path.includes('louisville')) currentTown = "Louisville";
    else if (path.includes('xenia')) currentTown = "Xenia";
    else if (path.includes('sailor-springs')) currentTown = "Sailor Springs";

    // 3. COLOR LOCKS
    const townColors = {
        "Flora": { bg: "#0c0b82", text: "#fe4f00" },
        "Louisville": { bg: "#010101", text: "#eb1c24" },
        "Clay City": { bg: "#0c30f0", text: "#8a8a88" },
        "Xenia": { bg: "#000000", text: "#fdb813" },
        "Sailor Springs": { bg: "#000000", text: "#a020f0" },
        "Clay County": { bg: "#333333", text: "#ffffff" }
    };

    fetch(jsonUrl)
        .then(response => response.json())
        .then(data => {
            // 4. LOGIC FOR FULL ARTICLE PAGE
            if (isFullArticlePage && targetArticleId) {
                const item = data.find(s => s.id === targetArticleId);
                if (item) renderFullStory(item);
                return;
            }

            // 5. LOGIC FOR TOWN SUMMARIES
            const filteredNews = data.filter(item => {
                if (!currentTown) return true; // Show all if on main supportmylocalcommunity.com
                return item.tags.includes(currentTown) || item.tags.includes("Clay County");
            });

            filteredNews.forEach(item => {
                if (processedIds.has(item.id)) return;
                processedIds.add(item.id);
                renderSummary(item);
            });
        });

    function renderSummary(item) {
        if (!summaryContainer) return;
        const mainBG = item.tags.length > 1 ? "#333333" : (townColors[item.tags[0]]?.bg || "#333333");
        const tagsHTML = item.tags.map(t => `<span class="tag" style="background:${townColors[t]?.bg || '#333'}; color:${townColors[t]?.text || '#fff'}; border:1px solid ${townColors[t]?.text || '#fff'}; padding:2px 8px; border-radius:4px; margin-right:5px; font-size:0.8em; font-weight:bold;">${t}</span>`).join('');
        
        summaryContainer.innerHTML += `
            <div class="summary-box" style="border-top: 10px solid ${mainBG}; background:#fdfdfb; padding:20px; margin-bottom:30px; box-shadow:2px 2px 10px rgba(0,0,0,0.1); font-family:serif;">
                <h3 style="text-transform:uppercase; margin-top:0;">${item.title}</h3>
                <div style="margin-bottom:12px;">${tagsHTML}</div>
                <p style="font-size:1.1rem; color:#444;">${item.summary || (item.full_story.substring(0, 150) + '...')}</p>
                <a href="${hubUrl}?id=${item.id}" style="color:${mainBG}; font-weight:bold; text-decoration:underline;">Read Full Story ↓</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const mainBG = townColors[item.tags[0]]?.bg || "#333333";
        fullContainer.innerHTML = `
            <div class="full-story-display" style="border-left:15px solid ${mainBG}; padding-left:25px; font-family:serif;">
                <h1 style="color:${mainBG}; font-size:2.5rem; text-transform:uppercase;">${item.title}</h1>
                <div class="story-body" style="white-space:pre-wrap; font-size:1.2rem; line-height:1.8;">${item.full_story}</div>
                <hr>
                <a href="javascript:history.back()" style="color:#666; font-weight:bold;">← Back to News Feed</a>
            </div>`;
    }
});
