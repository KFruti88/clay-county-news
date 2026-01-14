document.addEventListener('DOMContentLoaded', async () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // 1. ATOMIC CHICAGO TIME SYNC
    let trueTime = new Date();
    try {
        const timeRes = await fetch('https://worldtimeapi.org/api/timezone/America/Chicago');
        const timeData = await timeRes.json();
        trueTime = new Date(timeData.datetime);
    } catch (e) {
        console.warn("Atomic sync failed, using device time.");
    }

    // Update Newspaper Info Bar (Date, Clock, Weather Preview)
    updateNewspaperHeader(trueTime);

    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${trueTime.getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // 2. TOWN THEMES (Lowercase for URL matching)
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
    if (currentURL.includes('flora')) themeKey = "flora";
    else if (currentURL.includes('louisville')) themeKey = "louisville";
    else if (currentURL.includes('clay-city')) themeKey = "clay-city";
    else if (currentURL.includes('xenia')) themeKey = "xenia";
    else if (currentURL.includes('sailor-springs')) themeKey = "sailor-springs";

    document.body.style.backgroundColor = townThemes[themeKey].bg;

    // 3. FETCH & RENDER NEWS
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

            if (fullContainer) {
                fullContainer.innerHTML = ''; 
                filteredData.forEach(item => renderFullStory(item));
                handleScroll();
            } else if (summaryContainer) {
                summaryContainer.innerHTML = ''; 
                const townNews = filteredData.filter(item => 
                    themeKey === "default" || item.tags.some(t => t.toLowerCase() === themeKey) || item.tags.includes("Clay County")
                );
                townNews.forEach(item => renderSummary(item));
            }
        });

    // --- NEWSPAPER HEADER FUNCTIONS ---
    async function updateNewspaperHeader(t) {
        // Date (Left)
        const dOptions = { month: 'long', day: 'numeric', year: 'numeric' };
        document.getElementById('current-date').innerText = t.toLocaleDateString('en-US', dOptions);

        // Chicago Clock (Middle)
        const tOptions = { hour: '2-digit', minute: '2-digit', hour12: true };
        document.getElementById('atomic-chicago-time').innerText = t.toLocaleTimeString('en-US', tOptions);

        // Flora Airport Weather Preview (Right)
        try {
            const wRes = await fetch('https://api.open-meteo.com/v1/forecast?latitude=38.6672&longitude=-88.4523&current_weather=true');
            const wData = await wRes.json();
            const temp = Math.round(wData.current_weather.temperature * 9/5 + 32);
            const code = wData.current_weather.weathercode;

            const weatherMap = {
                0: { text: "Sunny", class: "sunny" },
                1: { text: "Mainly Clear", class: "sunny" },
                2: { text: "Partly Cloudy", class: "cloudy" },
                3: { text: "Overcast", class: "cloudy" },
                default: { text: "Rainy", class: "rainy" }
            };

            const status = weatherMap[code] || weatherMap['default'];
            const weatherEl = document.getElementById('airport-weather');
            weatherEl.className = `meta-item ${status.class}`;
            document.getElementById('temp-val').innerText = `${temp}°F`;
            document.getElementById('condition-val').innerText = status.text;
        } catch (e) { console.error("Weather failed"); }
    }

    function renderSummary(item) {
        if (!summaryContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; height:auto; border-radius:12px; margin-bottom:15px; object-fit: cover;">` : '';
        
        summaryContainer.innerHTML += `
            <div class="summary-box" style="width: 90%; max-width: 1200px; margin: 0 auto 20px auto; background: white; padding: 20px; border-radius: 8px; box-sizing: border-box; overflow-wrap: break-word;">
                <h3 style="margin-top: 0; color: #1a1a1a;">${formatMoney(item.title)}</h3>
                <p style="font-size: 0.9rem; color: #555;">${item.date}</p>
                ${imgHTML}
                <p style="line-height: 1.6; color: #333;">${formatMoney(item.full_story.substring(0, 180))}...</p>
                <a href="${hubUrl}?id=${item.id}" target="_top" class="read-more-btn" style="display: inline-block; padding: 10px 20px; background: ${townThemes[themeKey].bg}; color: white; text-decoration: none; border-radius: 4px;">Read Full Story</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; height:auto; border-radius:12px; margin-bottom:20px; object-fit: cover;">` : '';

        fullContainer.innerHTML += `
            <article id="${item.id}" class="full-story-display" style="width: 100%; max-width: 800px; margin: 0 auto 30px auto; background: white; padding: 30px; border-radius: 12px; box-sizing: border-box; overflow-wrap: break-word;">
                <h1 style="color: #1a1a1a; word-wrap: break-word;">${formatMoney(item.title)}</h1>
                <p style="text-align: center; font-weight: bold; color: #666;">${item.date} | ${item.tags.join(' | ')}</p>
                ${imgHTML}
                <div class="story-body" style="white-space: pre-wrap; line-height: 1.8; color: #222;">${formatMoney(item.full_story)}</div>
            </article>`;
    }

    function formatMoney(text) {
        if (!text) return "";
        return text.replace(/(\$\d+(?:,\d{3})*(?:\.\d{2})?)/g, '<span style="white-space: nowrap; font-weight: bold;">$1</span>');
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

// Weather Tab breakout
function openWeatherTab() {
    window.open("https://www.accuweather.com/en/us/flora/62839/weather-forecast/332851", "_top");
}
