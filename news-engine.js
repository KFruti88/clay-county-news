document.addEventListener('DOMContentLoaded', async () => {
    // --- 1. HARLOCK SELECTION (HARD ENFORCEMENT) ---
    // Rule: Town sites must have id="town-summaries". Hub must have id="full-news-feed".
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // --- 2. INSTANT PLUGINS (Weather & Time) ---
    let trueTime = new Date();
    updateNewspaperHeader(trueTime); // Immediate draw to prevent "Syncing..." hang

    try {
        const timeRes = await fetch('https://worldtimeapi.org/api/timezone/America/Chicago');
        const timeData = await timeRes.json();
        trueTime = new Date(timeData.datetime);
        updateNewspaperHeader(trueTime); // Re-sync to Atomic Chicago Time
    } catch (e) { 
        console.warn("Atomic sync failed - Calculating Central Time from system clock."); 
    }

    // --- 3. THEME LOCK ---
    const townThemes = {
        "flora": "#0c0b82", "louisville": "#010101", "clay-city": "#0c30f0",
        "xenia": "#000000", "sailor-springs": "#000000", "default": "#0c71c3"
    };
    const currentURL = window.location.href.toLowerCase();
    let themeKey = "default";
    const slugs = ["flora", "louisville", "clay-city", "xenia", "sailor-springs"];
    slugs.forEach(slug => { if (currentURL.includes(slug)) themeKey = slug; });
    document.body.style.backgroundColor = townThemes[themeKey];

    // --- 4. DATA ENGINE (CLAY COUNTY ONLY) ---
    const jsonUrl = `news_data.json?v=${trueTime.getTime()}`;
    const hubUrl = "https://www.supportmylocalcommunity.com/local-news.html";

    fetch(jsonUrl).then(res => res.json()).then(data => {
        const filteredData = data.filter(item => {
            const isForThisTown = item.tags.some(t => t.toLowerCase() === themeKey);
            const isClayCounty = item.tags.some(t => t.toLowerCase() === "clay county");
            const isPrimary = item.is_primary === true;
            
            // HARD BLOCK: Fairfield/Wayne County Filter
            const isNotWayne = !item.title.includes("Fairfield") && !item.title.includes("Wayne County") && !item.title.includes("Cisne");

            return (isForThisTown || isClayCounty || isPrimary) && isNotWayne;
        });

        // --- HARD RENDER LOCK ---
        if (summaryContainer) {
            // RULE: Town Site = Summary Mode Only
            summaryContainer.innerHTML = ''; 
            filteredData.forEach(item => {
                const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:15px; object-fit: cover;">` : '';
                summaryContainer.innerHTML += `
                    <div class="summary-box">
                        <h3>${formatMoney(item.title)}</h3>
                        <p style="font-size:0.9rem; color:#555;">${item.date}</p>
                        ${imgHTML}
                        <p>${formatMoney(item.full_story.substring(0, 180))}...</p>
                        <a href="${hubUrl}?id=${item.id}" target="_top" class="read-more-btn">Read Full Story</a>
                    </div>`;
            });
        } else if (fullContainer) {
            // RULE: Hub Site = Full Story Mode Only
            fullContainer.innerHTML = ''; 
            filteredData.forEach(item => {
                const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:20px; object-fit: cover;">` : '';
                fullContainer.innerHTML += `
                    <article id="${item.id}" class="full-story-display">
                        <h1>${formatMoney(item.title)}</h1>
                        <p style="text-align:center; font-weight:bold; color:#666;">${item.date} | ${item.tags.join(' | ')}</p>
                        ${imgHTML}
                        <div class="story-body" style="white-space: pre-wrap;">${formatMoney(item.full_story)}</div>
                    </article>`;
            });
            // RULE: Auto-Scroll with 500ms Render Safety
            setTimeout(() => { handleScroll(); }, 500);
        }
    });

    // --- 5. UTILITY FUNCTIONS ---
    function handleScroll() {
        const targetId = new URLSearchParams(window.location.search).get('id'); 
        if (targetId) {
            const el = document.getElementById(targetId);
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function formatMoney(text) {
        if (!text) return "";
        return text.replace(/(\$\d+(?:,\d{3})*(?:\.\d{2})?)/g, '<span style="white-space: nowrap; font-weight: bold;">$1</span>');
    }

    async function updateNewspaperHeader(t) {
        const dEl = document.getElementById('current-date');
        const cEl = document.getElementById('atomic-chicago-time');
        const tEl = document.getElementById('temp-val');
        const wEl = document.getElementById('condition-val');

        // LOCK: Permanent Central Time Enforcement
        const centralOptions = { 
            timeZone: 'America/Chicago', 
            hour: '2-digit', 
            minute: '2-digit', 
            hour12: true 
        };

        if (dEl) dEl.innerText = t.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', timeZone: 'America/Chicago' });
        if (cEl) cEl.innerText = t.toLocaleTimeString('en-US', centralOptions);
        
        try {
            const wRes = await fetch('https://api.open-meteo.com/v1/forecast?latitude=38.6672&longitude=-88.4523&current_weather=true');
            const wData = await wRes.json();
            const temp = Math.round(wData.current_weather.temperature * 9/5 + 32);
            if (tEl) tEl.innerText = `${temp}°F`;
            if (wEl) wEl.innerText = "Flora Airport";
        } catch (e) { 
            if (tEl) tEl.innerText = "--°F"; 
        }
    }
});

function openWeatherTab() { window.open("https://www.accuweather.com/en/us/flora/62839/weather-forecast/332851", "_top"); }
