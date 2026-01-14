document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // Cache busting ensures fresh news across both domains every time the page loads
    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${new Date().getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // THEME MAP: Using lowercase keys to ensure perfect URL matching
    const townThemes = {
        "flora": { bg: "#0c0b82" },        // Deep Navy
        "louisville": { bg: "#010101" },   // Black
        "clay-city": { bg: "#0c30f0" },    // Blue
        "xenia": { bg: "#000000" },        // Black
        "sailor-springs": { bg: "#000000" }, 
        "obituary": { bg: "#333333" },
        "fire dept": { bg: "#ff4500" },
        "police/pd": { bg: "#00008b" },
        "default": { bg: "#0c71c3" }       
    };

    // 1. DETECTION: Checks the address bar for town name using lowercase for accuracy
    const currentURL = window.location.href.toLowerCase();
    let themeKey = "default";

    if (currentURL.includes('flora')) themeKey = "flora";
    else if (currentURL.includes('louisville')) themeKey = "louisville";
    else if (currentURL.includes('clay-city')) themeKey = "clay-city";
    else if (currentURL.includes('xenia')) themeKey = "xenia";
    else if (currentURL.includes('sailor-springs')) themeKey = "sailor-springs";

    // APPLY BACKGROUND THEME BEHIND THE ARTICLES
    document.body.style.backgroundColor = townThemes[themeKey].bg;

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
                handleScroll(); // Trigger the scroll drop once stories are loaded
            } else if (summaryContainer) {
                summaryContainer.innerHTML = ''; 
                // Matching news tags to our lowercase themeKey
                const townNews = filteredData.filter(item => 
                    themeKey === "default" || item.tags.some(t => t.toLowerCase() === themeKey) || item.tags.includes("Clay County")
                );
                townNews.forEach(item => renderSummary(item));
            }
        })
        .catch(err => console.error("News Load Error:", err));

    function renderSummary(item) {
        if (!summaryContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:15px;">` : '';
        
        // target="_top" forces the link to break out of the box and open the full hub site
        summaryContainer.innerHTML += `
            <div class="summary-box">
                <h3>${item.title}</h3>
                <p style="font-size: 0.9rem; color: #555;">${item.date}</p>
                ${imgHTML}
                <p>${item.full_story.substring(0, 180)}...</p>
                <a href="${hubUrl}?id=${item.id}" target="_top" class="read-more-btn">Read Full Story</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:20px;">` : '';

        // FIXED: This ID matches the URL ?id= so the scroll function works
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

    // SCROLL FUNCTION: Finds the Article ID and drops the user to it
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
