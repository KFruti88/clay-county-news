document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    // Cache busting ensures fresh news across both domains every time the page loads
    const jsonUrl = `https://kfruti88.github.io/clay-county-news/news_data.json?v=${new Date().getTime()}`;
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    const townThemes = {
        "Flora": { bg: "#0c0b82" },        // Deep Navy
        "Louisville": { bg: "#010101" },   // Black
        "Clay City": { bg: "#0c30f0" },    // Blue
        "Xenia": { bg: "#000000" },        // Black
        "Sailor Springs": { bg: "#000000" }, // Black
        "Obituary": { bg: "#333333" },
        "Fire Dept": { bg: "#ff4500" },
        "Police/PD": { bg: "#00008b" },
        "Default": { bg: "#0c71c3" }       // Light Blue fallback
    };

    // 1. DETECTION: Checks the address bar to identify the town and set background
    const currentURL = window.location.href.toLowerCase();
    let currentTown = "Default";

    if (currentURL.includes('flora')) currentTown = "Flora";
    else if (currentURL.includes('louisville')) currentTown = "Louisville";
    else if (currentURL.includes('clay-city')) currentTown = "Clay City";
    else if (currentURL.includes('xenia')) currentTown = "Xenia";
    else if (currentURL.includes('sailor-springs')) currentTown = "Sailor Springs";

    // APPLY BACKGROUND THEME
    document.body.style.backgroundColor = townThemes[currentTown].bg;

    const isHubMode = !!fullContainer;

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

            if (isHubMode) {
                fullContainer.innerHTML = ''; 
                filteredData.forEach(item => renderFullStory(item));
                handleScroll(); // Trigger the scroll drop once stories are loaded
            } else if (summaryContainer) {
                summaryContainer.innerHTML = ''; 
                const townNews = filteredData.filter(item => 
                    currentTown === "Default" || item.tags.includes(currentTown) || item.tags.includes("Clay County")
                );
                townNews.forEach(item => renderSummary(item));
            }
        })
        .catch(err => console.error("News Load Error:", err));

    function renderSummary(item) {
        if (!summaryContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:15px;">` : '';
        
        // target="_top" forces the link to break out of the box and open the full hub site
        summaryContainer.innerHTML += `
            <div class="summary-box">
                <h3>${item.title}</h3>
                <p style="font-size: 0.9rem; color: #555;">${item.date}</p>
                ${imgHTML}
                <p>${item.full_story.substring(0, 180)}...</p>
                <a href="${hubUrl}?id=${item.id}" target="_top" class="read-more-btn">Read Full Story</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:20px;">` : '';

        // FIXED: Added id="${item.id}" so the handleScroll function can find this specific article
        fullContainer.innerHTML += `
            <article id="${item.id}" class="full-story-display">
                <h1>${item.title}</h1>
                <p style="text-align: center; font-weight: bold; color: #666;">
                    ${item.date} | ${item.tags.join(' | ')}
                </p>
                ${imgHTML}
                <div class="story-body" style="white-space: pre-wrap;">${item.full_story}</div>
            </article>`;
    }

    // THE RECOMMENDED SCROLL FUNCTION: Drops the user directly to the story
    function handleScroll() {
        const params = new URLSearchParams(window.location.search);
        const targetId = params.get('id'); // Looks for the ID in the hub URL
        if (targetId) {
            let attempts = 0;
            const scrollInterval = setInterval(() => {
                const element = document.getElementById(targetId);
                if (element) {
                    clearInterval(scrollInterval);
                    // Performs the smooth "drop" to the article
                    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else if (attempts++ > 60) clearInterval(scrollInterval);
            }, 100);
        }
    }
});
