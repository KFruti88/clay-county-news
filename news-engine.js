document.addEventListener('DOMContentLoaded', async () => {
    // --- ZONE 1: CORE SELECTION (LOCKED) ---
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // ATOMIC CHICAGO TIME: Standardizes time across all devices
    let trueTime = new Date();
    try {
        const timeRes = await fetch('https://worldtimeapi.org/api/timezone/America/Chicago');
        const timeData = await timeRes.json();
        trueTime = new Date(timeData.datetime);
        console.log("Atomic Chicago Time Synced:", trueTime.toLocaleString());
    } catch (e) { 
        console.warn("Atomic sync failed, using device clock."); 
    }

    // Run Header Plugins (Clock/Weather)
    updateNewspaperHeader(trueTime);

    // Atomic timestamp for cache busting
    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${trueTime.getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // --- ZONE 2: TOWN THEME & SLUG LOCK (LOCKED) ---
    const townThemes = {
        "flora": { bg: "#0c0b82" }, 
        "louisville": { bg: "#010101" },
        "clay-city": { bg: "#0c30f0" }, 
        "xenia": { bg: "#000000" },
        "sailor-springs": { bg: "#000000" }, 
        "default": { bg: "#0c71c3" }
    };

    const currentURL = window.location.href.toLowerCase();
    let themeKey = "default";
    let isTownSite = false;

    // Detect Slugs to lock Town Summary behavior
    const slugs = ["flora", "louisville", "clay-city", "xenia", "sailor-springs"];
    slugs.forEach(slug => {
        if (currentURL.includes(slug)) { 
            themeKey = slug; 
            isTownSite = true; 
        }
    });

    // Apply color to body (Divi will inherit this)
    document.body.style.backgroundColor = (townThemes[themeKey] || townThemes["default"]).bg;

    // --- ZONE 3: DATA FETCH & RENDER (LOCKED) ---
    fetch(jsonUrl).then(res => res.json()).then(data => {
        const clayTownList = ["flora", "louisville", "clay-city", "xenia", "sailor-springs"];
        
        const filteredData = data.filter(item => {
            // General News Logic: If an article has NO town tags, it shows everywhere
            const hasTownTag = item.tags.some(tag => clayTownList.includes(tag.toLowerCase()));
            const isForThisTown = item.tags.some(t => t.toLowerCase() === themeKey);
            const isGeneralNews = !hasTownTag; 
            const isCountyWide = item.tags.some(t => t.toLowerCase() === "clay county");
            const isPrimary = item.is_primary === true;
            const isNotWayne = !item.title.includes("Cisne") && !item.title.includes("Wayne County");

            return (isForThisTown || isGeneralNews || isCountyWide || isPrimary) && isNotWayne;
        });

        // LOCK: If town slug detected, ONLY use Summary View
        if (isTownSite && summaryContainer) {
            summaryContainer.innerHTML = ''; 
            filteredData.forEach(item => renderSummary(item));
        } 
        // LOCK: Main Hub uses Full Story View
        else if (fullContainer) {
            fullContainer.innerHTML = ''; 
            filteredData.forEach(item => renderFullStory(item));
            
            // FIXED SCROLL: Waits for Divi modules to render
            setTimeout(() => { handleScroll(); }, 500); 
        }
    });

    // --- ZONE 4: THE RENDERERS (LOCKED LAYOUT) ---
    function renderSummary(item) {
        if (!summaryContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; height:auto; border-radius:12px; margin-bottom:15px; object-fit: cover;">` : '';
        
        // BREAKOUT LOCK: target="_top" forces link to open main hub
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
                <p style="text-align: center; font-weight: bold; color: #666;">${item.date} | ${item.tags.join(' | ')}</p>
                ${imgHTML}
                <div class="story-body" style="white-space: pre-wrap;">${formatMoney(item.full_story)}</div>
            </article>`;
    }

    // --- ZONE 5: UTILITIES & PLUGINS ---
    function handleScroll() {
        const params = new URLSearchParams(window.location.search);
        const targetId = params.get('id'); 
        if (targetId) {
            const element = document.getElementById(targetId);
            if (element) { 
                element.scrollIntoView({ behavior: 'smooth', block: 'start' }); 
            }
        }
    }

    function formatMoney(text) {
        if (!text) return "";
        // Keeps dollar amounts on one line
        return text.replace(/(\$\d+(?:,\d{3})*(?:\.\d{2})?)/g, '<span style="white-space: nowrap; font-weight: bold;">$1</span>');
    }

    async function updateNewspaperHeader(t) {
        const dEl = document.getElementById('current-date');
        const cEl = document.getElementById('atomic-chicago-time');
        
        if (dEl) dEl.innerText = t.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
        if (cEl) cEl.innerText = t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
        
        try {
            // Flora Airport Weather Sync
            const wRes = await fetch('https://api.open-meteo.com/v1/forecast?latitude=38.6672&longitude=-88.4523&current_weather=true');
            const wData = await wRes.json();
            const temp = Math.round(wData.current_weather.temperature * 9/5 + 32);
            document.getElementById('temp-val').innerText = `${temp}°F`;
            document.getElementById('condition-val').innerText = "Flora Airport";
        } catch (e) { 
            console.error("Weather plugin failed to update.");
        }
    }
});

function openWeatherTab() {
    window.open("https://www.accuweather.com/en/us/flora/62839/weather-forecast/332851", "_top");
}
