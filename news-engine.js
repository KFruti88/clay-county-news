document.addEventListener('DOMContentLoaded', async () => {
    // --- ZONE 1: CORE SELECTION (HARD LOCK) ---
    // The script identifies the site type based on which ID is present in your HTML
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // ATOMIC CHICAGO TIME: Standardizes time for all domains
    let trueTime = new Date();
    try {
        const timeRes = await fetch('https://worldtimeapi.org/api/timezone/America/Chicago');
        const timeData = await timeRes.json();
        trueTime = new Date(timeData.datetime);
    } catch (e) { console.warn("Atomic sync failed, using backup time."); }

    // Run Header Plugins (Date/Clock/Weather)
    updateNewspaperHeader(trueTime);

    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${trueTime.getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // --- ZONE 2: TOWN THEME LOCK ---
    const townThemes = {
        "flora": "#0c0b82", "louisville": "#010101", "clay-city": "#0c30f0",
        "xenia": "#000000", "sailor-springs": "#000000", "default": "#0c71c3"
    };
    const currentURL = window.location.href.toLowerCase();
    let themeKey = "default";
    const slugs = ["flora", "louisville", "clay-city", "xenia", "sailor-springs"];
    slugs.forEach(slug => { if (currentURL.includes(slug)) themeKey = slug; });
    document.body.style.backgroundColor = townThemes[themeKey];

    // --- ZONE 3: DATA FETCH & CLAY COUNTY FILTER ---
    fetch(jsonUrl).then(res => res.json()).then(data => {
        const filteredData = data.filter(item => {
            // Must match the town, be general Clay County, or be a primary story
            const isForThisTown = item.tags.some(t => t.toLowerCase() === themeKey);
            const isClayCounty = item.tags.some(t => t.toLowerCase() === "clay county");
            const isPrimary = item.is_primary === true;
            
            // HARD BLOCK: Prevents Fairfield/Wayne County/Cisne from appearing
            const isNotWayne = !item.title.includes("Fairfield") && !item.title.includes("Wayne County") && !item.title.includes("Cisne");

            return (isForThisTown || isClayCounty || isPrimary) && isNotWayne;
        });

        // --- ZONE 4: THE HARD-LOCK RENDER ---
        
        // RULE 1: If "town-summaries" exists, FORCED summary mode
        if (summaryContainer) {
            summaryContainer.innerHTML = ''; 
            filteredData.forEach(item => {
                const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:15px; object-fit: cover;">` : '';
                summaryContainer.innerHTML += `
                    <div class="summary-box">
                        <h3>${formatMoney(item.title)}</h3>
                        <p style="font-size: 0.9rem; color: #555;">${item.date}</p>
                        ${imgHTML}
                        <p>${formatMoney(item.full_story.substring(0, 180))}...</p>
                        <a href="${hubUrl}?id=${item.id}" target="_top" class="read-more-btn">Read Full Story</a>
                    </div>`;
            });
        } 
        
        // RULE 2: If "full-news-feed" exists, FORCED full story mode
        else if (fullContainer) {
            fullContainer.innerHTML = ''; 
            filteredData.forEach(item => {
                const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:20px; object-fit: cover;">` : '';
                fullContainer.innerHTML += `
                    <article id="${item.id}" class="full-story-display">
                        <h1>${formatMoney(item.title)}</h1>
                        <p style="text-align: center; font-weight: bold; color: #666;">${item.date} | ${item.tags.join(' | ')}</p>
                        ${imgHTML}
                        <div class="story-body" style="white-space: pre-wrap;">${formatMoney(item.full_story)}</div>
                    </article>`;
            });
            
            // RULE 3: HARD SCROLL LOCK (500ms delay to ensure render)
            setTimeout(() => { handleScroll(); }, 500);
        }
    });

    // --- ZONE 5: UTILITIES ---
    
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
        return text.replace(/(\$\d+(?:,\d{3})*(?:\.\d{2})?)/g, '<span style="white-space: nowrap; font-weight: bold;">$1</span>');
    }

    async function updateNewspaperHeader(t) {
        const dEl = document.getElementById('current-date');
        const cEl = document.getElementById('atomic-chicago-time');
        if (dEl) dEl.innerText = t.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
        if (cEl) cEl.innerText = t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
        
        try {
            const wRes = await fetch('https://api.open-meteo.com/v1/forecast?latitude=38.6672&longitude=-88.4523&current_weather=true');
            const wData = await wRes.json();
            const temp = Math.round(wData.current_weather.temperature * 9/5 + 32);
            if (document.getElementById('temp-val')) document.getElementById('temp-val').innerText = `${temp}°F`;
            if (document.getElementById('condition-val')) document.getElementById('condition-val').innerText = "Flora Airport";
        } catch (e) { }
    }
});

function openWeatherTab() {
    window.open("https://www.accuweather.com/en/us/flora/62839/weather-forecast/332851", "_top");
}
