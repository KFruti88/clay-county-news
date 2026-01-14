document.addEventListener('DOMContentLoaded', async () => {
    // --- ZONE 1: CORE SELECTION ---
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // ATOMIC CHICAGO TIME
    let trueTime = new Date();
    try {
        const timeRes = await fetch('https://worldtimeapi.org/api/timezone/America/Chicago');
        const timeData = await timeRes.json();
        trueTime = new Date(timeData.datetime);
    } catch (e) { console.warn("Atomic sync failed"); }

    updateNewspaperHeader(trueTime);

    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${trueTime.getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // --- ZONE 2: THE HARD DOMAIN & SLUG LOCK ---
    const townThemes = {
        "flora": { bg: "#0c0b82" }, "louisville": { bg: "#010101" },
        "clay-city": { bg: "#0c30f0" }, "xenia": { bg: "#000000" },
        "sailor-springs": { bg: "#000000" }, "default": { bg: "#0c71c3" }       
    };

    const currentURL = window.location.href.toLowerCase();
    const currentHost = window.location.hostname.toLowerCase();
    let themeKey = "default";
    let isTownSite = false;

    // FORCED CHECK: If we are on ourflora.com OR the GitHub town preview
    if (currentHost.includes('ourflora.com') || currentURL.includes('clay-county-news')) {
        themeKey = "flora"; 
        isTownSite = true;
    }

    // OVERRIDE: If the URL actually contains "local-news", it is NEVER a town site
    if (currentURL.includes('local-news')) {
        isTownSite = false;
    }

    document.body.style.backgroundColor = townThemes[themeKey].bg;

    // --- ZONE 3: FETCH & RENDER ---
    fetch(jsonUrl).then(res => res.json()).then(data => {
        const clayTownList = ["flora", "louisville", "clay-city", "xenia", "sailor-springs"];
        
        const filteredData = data.filter(item => {
            const hasTownTag = item.tags.some(tag => clayTownList.includes(tag.toLowerCase()));
            const isForThisTown = item.tags.some(t => t.toLowerCase() === themeKey);
            const isGeneralNews = !hasTownTag; 
            const isCountyWide = item.tags.some(t => t.toLowerCase() === "clay county");
            const isPrimary = item.is_primary === true;
            const isNotWayne = !item.title.includes("Cisne") && !item.title.includes("Wayne County");

            return (isForThisTown || isGeneralNews || isCountyWide || isPrimary) && isNotWayne;
        });

        // THE FINAL LOCK
        if (isTownSite && summaryContainer) {
            // FORCING SUMMARY VIEW ONLY
            summaryContainer.innerHTML = ''; 
            filteredData.forEach(item => renderSummary(item));
        } else if (fullContainer) {
            // FORCING FULL HUB VIEW ONLY
            fullContainer.innerHTML = ''; 
            filteredData.forEach(item => renderFullStory(item));
            setTimeout(() => { handleScroll(); }, 500); 
        }
    });

    function renderSummary(item) {
        if (!summaryContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; height:auto; border-radius:12px; margin-bottom:15px; object-fit: cover;">` : '';
        // BREAKOUT LINK: Forces the user to the main hub
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

    function handleScroll() {
        const params = new URLSearchParams(window.location.search);
        const targetId = params.get('id'); 
        if (targetId) {
            const element = document.getElementById(targetId);
            if (element) { element.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
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
            document.getElementById('temp-val').innerText = `${temp}°F`;
            document.getElementById('condition-val').innerText = "Flora Airport";
        } catch (e) { }
    }
});

function openWeatherTab() {
    window.open("https://www.accuweather.com/en/us/flora/62839/weather-forecast/332851", "_top");
}
