document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // Cache busting: adds a unique timestamp to the end of the URL to fetch fresh data
    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${new Date().getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // THEME MAP: Branded colors for each town
    const townThemes = {
        "Flora": { bg: "#0c0b82", text: "#fe4f00" },
        "Louisville": { bg: "#010101", text: "#eb1c24" },
        "Clay City": { bg: "#0c30f0", text: "#8a8a88" },
        "Xenia": { bg: "#000000", text: "#fdb813" },
        "Sailor Springs": { bg: "#000000", text: "#a020f0" },
        "Obituary": { bg: "#333333", text: "#ffffff" },
        "Fire Dept": { bg: "#ff4500", text: "#ffffff" },
        "Police/PD": { bg: "#00008b", text: "#ffffff" },
        "Default": { bg: "#0c71c3", text: "#ffffff" } 
    };

    // 1. DETECT TOWN: Uses pathname to identify specific town pages
    const path = window.location.pathname.toLowerCase();
    let currentTown = "Default";

    if (path.includes('flora')) currentTown = "Flora";
    else if (path.includes('louisville')) currentTown = "Louisville";
    else if (path.includes('clay-city')) currentTown = "Clay City";
    else if (path.includes('xenia')) currentTown = "Xenia";
    else if (path.includes('sailor-springs')) currentTown = "Sailor Springs";

    // 2. APPLY THEME: Changes the page background based on detected town
    const pageTheme = townThemes[currentTown] || townThemes["Default"];
    document.body.style.backgroundColor = pageTheme.bg;
    document.body.style.color = pageTheme.text;

    const isHubMode = !!fullContainer;

    fetch(jsonUrl)
        .then(res => res.json())
        .then(data => {
            const clayTownList = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"];
            
            const filteredData = data.filter(item => {
                const isClay = item.tags.some(tag => clayTownList.includes(tag) || tag === "Clay County");
                const isPrimary = item.is_primary === true;
                const isNotWayne = !item.title.includes("Cisne") && !item.title.includes("Wayne County");
                return (isClay || isPrimary) && isNotWayne;
            });

            if (isHubMode) {
                fullContainer.innerHTML = ''; 
                filteredData.forEach(item => renderFullStory(item));
                handleScroll(); 
            } else if (summaryContainer) {
                summaryContainer.innerHTML = ''; 
                const townNews = filteredData.filter(item => 
                    currentTown === "Default" || item.tags.includes(currentTown) || item.tags.includes("Clay County")
                );
                townNews.forEach(item => renderSummary(item));
            }
        })
        .catch(err => console.error("News Load Error:", err));

    function renderSummary(item) {
        if (!summaryContainer) return;
        const itemTown = item.tags[0] || "Default";
        const itemTheme = townThemes[itemTown] || townThemes["Default"];
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:15px;">` : '';
        
        summaryContainer.innerHTML += `
            <div class="summary-box" style="border-top: 12px solid ${itemTheme.bg}; background-color: white; color: #1a1a1a; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: ${itemTheme.bg}; margin-top: 0;">${item.title}</h3>
                <p style="font-size: 0.9rem; color: #555;">${item.date}</p>
                ${imgHTML}
                <p>${item.full_story.substring(0, 180)}...</p>
                <a href="${hubUrl}?id=${item.id}" class="read-more-btn" style="background-color: ${itemTheme.bg}; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block;">Read Full Story</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const itemTown = item.tags[0] || "Default";
        const itemTheme = townThemes[itemTown] || townThemes["Default"];
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:20px;">` : '';

        fullContainer.innerHTML += `
            <article id="${item.id}" class="full-story-display" style="border-left: 20px solid ${itemTheme.bg}; background-color: white; color: #1a1a1a; padding: 30px; border-radius: 12px; margin-bottom: 30px;">
                <h1 style="color: ${itemTheme.bg};">${item.title}</h1>
                <p style="text-align: center; font-weight: bold; color: #666;">
                    ${item.date} | ${item.tags.join(' | ')}
                </p>
                ${imgHTML}
                <div class="story-body" style="white-space: pre-wrap;">${item.full_story}</div>
            </article>`;
    }

    function handleScroll() {
        const params = new URLSearchParams(window.location.search);
        const targetId = params.get('id');
        if (targetId) {
            let attempts = 0;
            const scrollInterval = setInterval(() => {
                const element = document.getElementById(targetId);
                if (element) {
                    clearInterval(scrollInterval);
                    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    element.style.boxShadow = "0 0 40px #ffff00"; 
                    setTimeout(() => { element.style.boxShadow = "none"; }, 3000);
                } else if (attempts++ > 60) clearInterval(scrollInterval);
            }, 100);
        }
    }
});
