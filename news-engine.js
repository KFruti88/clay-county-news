document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${new Date().getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    const townThemes = {
        "flora": { bg: "#0c0b82" },
        "louisville": { bg: "#010101" },
        "clay-city": { bg: "#0c30f0" },
        "xenia": { bg: "#000000" },
        "sailor-springs": { bg: "#000000" }, 
        "obituary": { bg: "#333333" },
        "fire dept": { bg: "#ff4500" },
        "police/pd": { bg: "#00008b" },
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

    function renderSummary(item) {
        if (!summaryContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; height:auto; border-radius:12px; margin-bottom:15px; object-fit: cover;">` : '';
        
        // Responsive logic: 90% mobile width, centering content for desktop
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

        // Desktop focused width (100% of container) with safe max-width
        fullContainer.innerHTML += `
            <article id="${item.id}" class="full-story-display" style="width: 100%; max-width: 800px; margin: 0 auto 30px auto; background: white; padding: 30px; border-radius: 12px; box-sizing: border-box; overflow-wrap: break-word;">
                <h1 style="color: #1a1a1a; word-wrap: break-word;">${formatMoney(item.title)}</h1>
                <p style="text-align: center; font-weight: bold; color: #666;">${item.date} | ${item.tags.join(' | ')}</p>
                ${imgHTML}
                <div class="story-body" style="white-space: pre-wrap; line-height: 1.8; color: #222;">${formatMoney(item.full_story)}</div>
            </article>`;
    }

    // Money protector: Keeps currency symbols and values glued together
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
