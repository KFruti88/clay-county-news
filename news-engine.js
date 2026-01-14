document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // Cache busting to ensure news is always fresh
    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${new Date().getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    const townThemes = {
        "Flora": { bg: "#0c0b82" },
        "Louisville": { bg: "#010101" },
        "Clay City": { bg: "#0c30f0" },
        "Xenia": { bg: "#000000" },
        "Sailor Springs": { bg: "#000000" },
        "Obituary": { bg: "#333333" },
        "Fire Dept": { bg: "#ff4500" },
        "Police/PD": { bg: "#00008b" },
        "Default": { bg: "#0c71c3" } 
    };

    // 1. Detect town from URL pathname to change the background BEHIND the articles
    const path = window.location.pathname.toLowerCase();
    let currentTown = "Default";

    if (path.includes('flora')) currentTown = "Flora";
    else if (path.includes('louisville')) currentTown = "Louisville";
    else if (path.includes('clay-city')) currentTown = "Clay City";
    else if (path.includes('xenia')) currentTown = "Xenia";
    else if (path.includes('sailor-springs')) currentTown = "Sailor Springs";

    // 2. CHANGE THE BACKGROUND COLOR BEHIND THE ARTICLE
    document.body.style.backgroundColor = townThemes[currentTown].bg;

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
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:15px;">` : '';
        
        // Keeping your original White/Black card style exactly as it was
        summaryContainer.innerHTML += `
            <div class="summary-box">
                <h3>${item.title}</h3>
                <p style="font-size: 0.9rem; color: #555;">${item.date}</p>
                ${imgHTML}
                <p>${item.full_story.substring(0, 180)}...</p>
                <a href="${hubUrl}?id=${item.id}" class="read-more-btn">Read Full Story</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:20px;">` : '';

        // Keeping your original White/Black article style exactly as it was
        fullContainer.innerHTML += `
            <article id="${item.id}" class="full-story-display">
                <h1>${item.title}</h1>
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
                } else if (attempts++ > 60) clearInterval(scrollInterval);
            }, 100);
        }
    }
});
