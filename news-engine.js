document.addEventListener('DOMContentLoaded', async () => {
    // --- ZONE 1: CORE ENGINE (LOCKED) ---
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    let trueTime = new Date();
    try {
        const timeRes = await fetch('https://worldtimeapi.org/api/timezone/America/Chicago');
        const timeData = await timeRes.json();
        trueTime = new Date(timeData.datetime);
    } catch (e) { console.warn("Atomic sync failed"); }

    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${trueTime.getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // --- ZONE 2: TOWN LAYOUT & COLORS (LOCKED) ---
    const townThemes = {
        "flora": { bg: "#0c0b82" }, "louisville": { bg: "#010101" },
        "clay-city": { bg: "#0c30f0" }, "xenia": { bg: "#000000" },
        "sailor-springs": { bg: "#000000" }, "default": { bg: "#0c71c3" }       
    };
    const currentURL = window.location.href.toLowerCase();
    let themeKey = "default";
    let isTownSite = false;

    if (currentURL.includes('flora')) { themeKey = "flora"; isTownSite = true; }
    else if (currentURL.includes('louisville')) { themeKey = "louisville"; isTownSite = true; }
    else if (currentURL.includes('clay-city')) { themeKey = "clay-city"; isTownSite = true; }
    else if (currentURL.includes('xenia')) { themeKey = "xenia"; isTownSite = true; }
    else if (currentURL.includes('sailor-springs')) { themeKey = "sailor-springs"; isTownSite = true; }

    document.body.style.backgroundColor = townThemes[themeKey].bg;

    // --- ZONE 3: PLUGINS (CLOCK & WEATHER) ---
    runHeaderPlugins(trueTime);

    // --- EXECUTION ---
    fetch(jsonUrl).then(res => res.json()).then(data => {
        const clayTownList = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"];
        const filteredData = data.filter(item => {
            const isClay = item.tags.some(tag => clayTownList.includes(tag) || tag === "Clay County");
            const isPrimary = item.is_primary === true;
            const isNotWayne = !item.title.includes("Cisne") && !item.title.includes("Wayne County");
            return (isClay || isPrimary) && isNotWayne;
        });

        if (isTownSite && summaryContainer) {
            summaryContainer.innerHTML = ''; 
            const townNews = filteredData.filter(item => 
                item.tags.some(t => t.toLowerCase() === themeKey) || item.tags.includes("Clay County")
            );
            townNews.forEach(item => renderSummary(item));
        } else if (fullContainer) {
            fullContainer.innerHTML = ''; 
            filteredData.forEach(item => renderFullStory(item));
            // FIXED SCROLL: Waits for full render before jumping
