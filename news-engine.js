document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    const summariesSection = document.getElementById('summaries-section');
    const processedIds = new Set();

    // 1. SETTINGS - THE MASTER SOURCE
    const jsonUrl = "https://kfruti88.github.io/clay-county-news/news_data.json";
    // This MUST match the folder on your website
    const hubUrl = "https://supportmylocalcommunity.com/local-news/"; 

    // 2. DETECTION
    const urlParams = new URLSearchParams(window.location.search);
    const targetArticleId = urlParams.get('id');
    const path = window.location.pathname.toLowerCase();

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
            // 3. FULL ARTICLE LOGIC
            if (targetArticleId) {
                const item = data.find(s => s.id === targetArticleId);
                if (item) {
                    if (summariesSection) summariesSection.style.display = 'none';
                    renderFullStory(item);
                    
                    // Auto-Scroll to top of article
                    setTimeout(() => {
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    }, 100);
                    return; 
                }
            }

            // 4. SUMMARY LIST LOGIC
            let townFilter = "";
            if (path.includes('flora')) townFilter = "Flora";
            else if (path.includes('clay-city')) townFilter = "Clay City";

            const filteredNews = data.filter(item => {
                if (!townFilter) return true; 
                return item.tags.includes(townFilter) || item.tags.includes("Clay County");
            });

            filteredNews.forEach(item => {
                if (processedIds.has(item.id)) return;
                processedIds.add(item.id);
                renderSummary(item);
            });
        })
        .catch(err => console.error("News Load Error:", err));

    function renderSummary(item) {
        if (!summaryContainer) return;
        const mainColor = townColors[item.tags[0]]?.bg || "#333333";
        const tagsHTML = item.tags.map(t => `<span class="tag" style="background:${townColors[t]?.bg || '#333'}; color:${townColors[t]?.text || '#fff'}; padding:2px 8px; border-radius:4px; margin-right:5px; font-size:0.7em; font-weight:bold; border:1px solid rgba(255,255,255,0.3);">${t}</span>`).join('');
        
        summaryContainer.innerHTML += `
            <div class="summary-box" style="border-top: 10px solid ${mainColor}; background:rgba(255,255,255,0.9); backdrop-filter:blur(10px); padding:30px; margin-bottom:30px; box-shadow:0 8px 32px rgba(0,0,0,0.1); border-radius:15px; transition:0.3s;">
                <h3 style="margin-top:0; text-transform:uppercase; font-size:1.5rem; font-weight:900;">${item.title}</h3>
                <div style="margin-bottom:15px;">${tagsHTML}</div>
                <p style="color:#333; font-size:1.15rem; line-height:1.6;">${item.summary || (item.full_story.substring(0, 150) + '...')}</p>
                <a href="${hubUrl}?id=${item.id}" style="display:inline-block; background:${mainColor}; color:white; padding:12px 25px; border-radius:50px; text-decoration:none; font-weight:bold; font-size:0.9rem; font-family:sans-serif;">Read Full Story ↓</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const mainColor = townColors[item.tags[0]]?.bg || "#333333";
        fullContainer.innerHTML = `
            <div class="full-story-display" style="border-left:15px solid ${mainColor}; padding:40px; background:#fff; border-radius:20px; box-shadow:0 20px 50px rgba(0,0,0,0.1);">
                <h1 style="color:${mainColor}; font-size:2.8rem; text-transform:uppercase; margin-top:0; font-weight:900;">${item.title}</h1>
                <div class="story-body" style="white-space:pre-wrap; font-size:1.35rem; line-height:2; font-family:serif; color:#222;">${item.full_story}</div>
                <hr style="margin:40px 0; opacity:0.1;">
                <a href="${hubUrl}" style="display:inline-block; color:#444; font-weight:bold; text-decoration:none; border:2px solid #444; padding:10px 25px; border-radius:50px; transition:0.3s;">← Back to News Feed</a>
            </div>`;
    }
});
