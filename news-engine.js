document.addEventListener('DOMContentLoaded', async () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // --- 1. ATOMIC CHICAGO TIME (LOCKED) ---
    let trueTime = new Date();
    try {
        const timeRes = await fetch('https://worldtimeapi.org/api/timezone/America/Chicago');
        const timeData = await timeRes.json();
        trueTime = new Date(timeData.datetime);
    } catch (e) { console.warn("Atomic sync failed, using device clock."); }

    updateNewspaperHeader(trueTime);

    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${trueTime.getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // --- 2. TOWN SLUG & COLOR LOCK ---
    const townThemes = {
        "flora": { bg: "#0c0b82" }, "louisville": { bg: "#010101" },
        "clay-city": { bg: "#0c30f0" }, "xenia": { bg: "#000000" },
        "sailor-springs": { bg: "#000000" }, "default": { bg: "#0c71c3" }       
    };
    const currentURL = window.location.href.toLowerCase();
    let themeKey = "default";
    let isTownSite = false;

    // Detect Town Slugs
    if (currentURL.includes('flora')) { themeKey = "flora"; isTownSite = true; }
    else if (currentURL.includes('louisville')) { themeKey = "louisville"; isTownSite = true; }
    else if (currentURL.includes('clay-city')) { themeKey = "clay-city"; isTownSite = true; }
    else if (currentURL.includes('xenia')) { themeKey = "xenia"; isTownSite = true; }
    else if (currentURL.includes('sailor-springs')) { themeKey = "sailor-springs"; isTownSite = true; }

    document.body.style.backgroundColor = townThemes[themeKey].bg;

    // --- 3. FETCH NEWS ---
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

            // TOWN SITE LOCK: Force Summary View
            if (isTownSite && summaryContainer) {
                summaryContainer.innerHTML = ''; 
                const townNews = filteredData.filter(item => 
                    item.tags.some(t => t.toLowerCase() === themeKey) || item.tags.includes("Clay County")
                );
                townNews.forEach(item => renderSummary(item));
            } 
            // MAIN HUB LOCK: Force Full Story View
            else if (fullContainer) {
                fullContainer.innerHTML = ''; 
                filteredData.forEach(item => renderFullStory(item));
                
                // --- FIXED SCROLL LOGIC ---
                // We wait 300ms to ensure the articles are fully rendered before scrolling
                setTimeout(() => { handleScroll(); }, 300);
            }
        });

    function renderSummary(item) {
        if (!summaryContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; height:auto; border-radius:12px; margin-bottom:15px; object-fit: cover;">` : '';
        
        // LOCKED: target="_top" forces breakout to local-news hub
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

    // --- SCROLL TO ARTICLE (LOCKED FIX) ---
    function handleScroll() {
        const params = new URLSearchParams(window.location.search);
        const targetId = params.get('id'); 
        if (targetId) {
            const element = document.getElementById(targetId);
            if (element) {
                // Smoothly drops the user directly to their article
                element.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }

    // --- REMAINDER OF UTILITIES ---
    async function updateNewspaperHeader(t) {
        if (document.getElementById('current-date')) {
            document.getElementById('current-date').innerText = t.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
        }
        if (document.getElementById('atomic-chicago-time')) {
            document.getElementById('atomic-chicago-time').innerText = t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
        }
        try {
            const wRes = await fetch('https://api.open-meteo.com/v1/forecast?latitude=38.6672&longitude=-88.4523&current_weather=true');
            const wData = await wRes.json();
            const temp = Math.round(wData.current_weather.temperature * 9/5 + 32);
            document.getElementById('temp-val').innerText = `${temp}°F`;
            document.getElementById('condition-val').innerText = "Flora Airport";
        } catch (e) { }
    }

    function formatMoney(text) {
        if (!text) return "";
        return text.replace(/(\$\d+(?:,\d{3})*(?:\.\d{2})?)/g, '<span style="white-space: nowrap; font-weight: bold;">$1</span>');
    }
});

function openWeatherTab() {
    window.open("https://www.accuweather.com/en/us/flora/62839/weather-forecast/332851", "_top");
}
