document.addEventListener('DOMContentLoaded', async () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // --- ZONE 1: CORE (LOCKED) ---
    let trueTime = new Date();
    try {
        const timeRes = await fetch('https://worldtimeapi.org/api/timezone/America/Chicago');
        const timeData = await timeRes.json();
        trueTime = new Date(timeData.datetime);
    } catch (e) { console.warn("Atomic sync failed"); }

    updateNewspaperHeader(trueTime);

    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${trueTime.getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // --- ZONE 2: HARD LOCK & MULTI-TOWN DETECTION ---
    const townThemes = {
        "flora": { bg: "#0c0b82" }, "louisville": { bg: "#010101" },
        "clay-city": { bg: "#0c30f0" }, "xenia": { bg: "#000000" },
        "sailor-springs": { bg: "#000000" }, "default": { bg: "#0c71c3" }       
    };

    const currentURL = window.location.href.toLowerCase();
    const currentHost = window.location.hostname.toLowerCase();
    let themeKey = "default";
    let isTownSite = false;

    // 1. Check for specific town slugs first (Works for GitHub & Hub)
    const slugs = ["flora", "louisville", "clay-city", "xenia", "sailor-springs"];
    slugs.forEach(slug => {
        if (currentURL.includes(slug)) { themeKey = slug; isTownSite = true; }
    });

    // 2. Domain Backup: Force Flora if on ourflora.com
    if (currentHost.includes('ourflora.com')) {
        themeKey = "flora"; 
        isTownSite = true;
    }

    // 3. Hub Override: Ensure local-news hub always shows full stories
    if (currentURL.includes('local-news')) {
        isTownSite = false;
    }

    document.body.style.backgroundColor = townThemes[themeKey].bg;

    // --- ZONE 3: DATA FETCH & CLAY COUNTY ONLY FILTER ---
    fetch(jsonUrl).then(res => res.json()).then(data => {
        const filteredData = data.filter(item => {
            // Match specific town OR match General "Clay County" tag
            const isForThisTown = item.tags.some(t => t.toLowerCase() === themeKey);
            const isGeneralClayCounty = item.tags.some(t => t.toLowerCase() === "clay county");
            const isPrimary = item.is_primary === true;

            // Strict Filter: Must be Clay County related
            const isClayContent = isForThisTown || isGeneralClayCounty || isPrimary;
            const isNotWayne = !item.title.includes("Cisne") && !item.title.includes("Wayne County");

            return isClayContent && isNotWayne;
        });

        // LOCK: Summaries for Towns, Full Stories for Hub
        if (isTownSite && summaryContainer) {
            summaryContainer.innerHTML = ''; 
            filteredData.forEach(item => renderSummary(item));
        } else if (fullContainer) {
            fullContainer.innerHTML = ''; 
            filteredData.forEach(item => renderFullStory(item));
            setTimeout(() => { handleScroll(); }, 500); 
        }
    });

    // --- ZONE 4: RENDERERS (LOCKED) ---
    function renderSummary(item) {
        if (!summaryContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; height:auto; border-radius:12px; margin-bottom:15px; object-fit: cover;">` : '';
        summaryContainer.innerHTML += `
            <div class="summary-box">
                <h3>${formatMoney(item.title)}</h3>
                <p style="font-size: 0.9rem; color: #555;">${item.date}</p>
                ${imgHTML}
                <p>${formatMoney(item.full_story.substring(0, 180))}...</p>
                <a href="${hubUrl}?id=${item.id}" target="_top" class="read-more-btn">Read Full Story</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; height:auto; border-radius:12px; margin-bottom:20px; object-fit: cover;">` : '';
        fullContainer.innerHTML += `
            <article id="${item.id}" class="full-story-display">
                <h1>${formatMoney(item.title)}</h1>
                <p style="text-align: center; font-weight: bold
