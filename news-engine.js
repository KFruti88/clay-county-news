// --- GLOBAL DATA STORE ---
let globalNewsData = [];

// --- UTILITY: Format Money ---
function formatMoney(text) {
    if (!text) return "";
    return text.replace(/(\$\d+(?:,\d{3})*(?:\.\d{2})?)/g, '<span style="white-space: nowrap; font-weight: bold;">$1</span>');
}

// --- MODAL CONTROLS ---
window.openNewsModal = function(id) {
    const item = globalNewsData.find(i => i.id === id);
    if (!item) return;

    document.getElementById('modalTitle').innerHTML = formatMoney(item.title);
    document.getElementById('modalDate').innerText = item.date + (item.tags ? " | " + item.tags.join(', ') : "");
    
    const imgEl = document.getElementById('modalImg');
    if (item.image) {
        imgEl.src = item.image;
        imgEl.style.display = 'block';
    } else {
        imgEl.style.display = 'none';
    }
    
    document.getElementById('modalBody').innerHTML = formatMoney(item.full_story);
    document.getElementById('newsModal').style.display = "block";
    document.body.style.overflow = "hidden"; // Prevent background scrolling
}

window.closeNewsModal = function() {
    document.getElementById('newsModal').style.display = "none";
    document.body.style.overflow = "auto"; // Restore scrolling
}

// --- INJECT MODAL HTML/CSS ---
function injectModalSystem() {
    if (document.getElementById('newsModal')) return;

    const style = document.createElement('style');
    style.innerHTML = `
        .news-modal { display: none; position: fixed; z-index: 9999; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.7); }
        .news-modal-content { background-color: #fdfbf7; margin: 5% auto; padding: 40px; border: 1px solid #333; width: 90%; max-width: 800px; border-radius: 0; position: relative; box-shadow: 10px 10px 0px rgba(0,0,0,0.3); animation: slideDown 0.3s ease-out; font-family: 'Merriweather', serif; }
        .news-close-btn { color: #000; float: right; font-size: 40px; font-weight: bold; cursor: pointer; line-height: 0.6; }
        .news-close-btn:hover { color: #555; }
        .news-modal-img { width: 100%; max-height: 400px; object-fit: contain; border: 1px solid #ccc; margin: 20px 0; display: block; background: #eee; filter: sepia(15%); }
        .news-modal-title { margin-top: 0; color: #111; font-size: 2.2rem; font-family: 'Playfair Display', serif; font-weight: 900; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }
        .news-modal-date { color: #444; font-style: italic; margin-bottom: 20px; font-family: 'Playfair Display', serif; font-size: 1rem; border-bottom: 1px solid #ccc; padding-bottom: 10px; }
        .news-modal-body { line-height: 1.8; font-size: 1.15rem; color: #222; white-space: pre-wrap; text-align: justify; }
        .read-more-btn { background: var(--town-gradient, #333); color: white; border: none; padding: 10px 15px; border-radius: 0; cursor: pointer; font-weight: bold; margin-top: 10px; width: 100%; font-family: 'Playfair Display', serif; text-transform: uppercase; letter-spacing: 1px; transition: transform 0.2s; }
        .read-more-btn:hover { transform: translateY(-2px); opacity: 0.9; }
        @keyframes slideDown { from { transform: translateY(-50px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        @media (max-width: 600px) { .news-modal-content { width: 95%; margin: 10% auto; padding: 20px; } .news-modal-title { font-size: 1.5rem; } }
    `;
    document.head.appendChild(style);

    const modalHtml = `
        <div id="newsModal" class="news-modal">
            <div class="news-modal-content">
                <span class="news-close-btn" onclick="closeNewsModal()">&times;</span>
                <h2 id="modalTitle" class="news-modal-title"></h2>
                <p id="modalDate" class="news-modal-date"></p>
                <img id="modalImg" class="news-modal-img" src="">
                <div id="modalBody" class="news-modal-body"></div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    window.addEventListener('click', function(event) {
        const modal = document.getElementById('newsModal');
        if (event.target == modal) closeNewsModal();
    });
}

// --- BACK TO TOP SYSTEM ---
function injectBackToTop() {
    if (document.getElementById('backToTopBtn')) return;

    const style = document.createElement('style');
    style.innerHTML = `
        #backToTopBtn {
            display: none;
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 999;
            font-size: 16px;
            border: none;
            outline: none;
            background: var(--town-gradient, #333);
            color: white;
            cursor: pointer;
            padding: 12px 18px;
            border-radius: 0; /* Sharp corners for newspaper look */
            box-shadow: 3px 3px 0 rgba(0,0,0,0.2);
            font-family: 'Playfair Display', serif;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: transform 0.2s;
        }
        #backToTopBtn:hover {
            transform: translateY(-2px);
            box-shadow: 5px 5px 0 rgba(0,0,0,0.3);
        }
    `;
    document.head.appendChild(style);

    const btn = document.createElement('button');
    btn.id = "backToTopBtn";
    btn.innerHTML = "&#8679; TOP";
    btn.onclick = function() {
        window.scrollTo({top: 0, behavior: 'smooth'});
    };
    document.body.appendChild(btn);

    window.addEventListener('scroll', function() {
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            btn.style.display = "block";
        } else {
            btn.style.display = "none";
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    injectModalSystem(); // Initialize Modal
    injectBackToTop();   // Initialize Back to Top

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
        "flora": { solid: "#0c0b82", gradient: "linear-gradient(135deg, #fe4f00, #0c0b82)" },
        "louisville": { solid: "#eb1c24", gradient: "linear-gradient(135deg, #eb1c24, #101010)" },
        "clay-city": { solid: "#0258a3", gradient: "linear-gradient(135deg, #0258a3, #8e8e8e)" },
        "xenia": { solid: "#000000", gradient: "linear-gradient(135deg, #000000, #ffd700)" },
        "iola": { solid: "#000000", gradient: "linear-gradient(135deg, #000000, #333333)" },
        "sailor-springs": { solid: "#000000", gradient: "linear-gradient(135deg, #000000, #800080)" },
        "default": { solid: "#0c71c3", gradient: "linear-gradient(135deg, #e0e0e0, #0c71c3)" }
    };
    const currentURL = window.location.href.toLowerCase();
    let themeKey = "default";
    const slugs = ["flora", "louisville", "clay-city", "xenia", "iola", "sailor-springs"];
    slugs.forEach(slug => { if (currentURL.includes(slug)) themeKey = slug; });
    
    const theme = townThemes[themeKey] || townThemes["default"];
    document.documentElement.style.setProperty('--town-color', theme.solid);
    document.documentElement.style.setProperty('--town-gradient', theme.gradient);

    // --- 4. DATA ENGINE (CLAY COUNTY ONLY) ---
    const jsonUrl = `news_data.json?v=${trueTime.getTime()}`;

    fetch(jsonUrl).then(res => res.json()).then(data => {
        const filteredData = data.filter(item => {
            // STRICT FILTER: Only allow specific Clay County towns
            const clayKeywords = ["flora", "clay city", "xenia", "louisville", "iola", "clay county", "sailor springs"];
            const textBlob = (item.title + " " + item.tags.join(" ") + " " + item.full_story).toLowerCase();
            const hasClayContent = clayKeywords.some(k => textBlob.includes(k));

            // HARD BLOCK: Fairfield/Wayne County Filter
            const isNotWayne = !item.title.includes("Fairfield") && !item.title.includes("Wayne County") && !item.title.includes("Cisne");

            return hasClayContent && isNotWayne;
        });

        globalNewsData = filteredData; // Store for modal access

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
                        <button class="read-more-btn" onclick="openNewsModal('${item.id}')">Read Full Story</button>
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
