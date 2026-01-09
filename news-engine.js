document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    const summariesSection = document.getElementById('summaries-section');
    const processedIds = new Set();

    const jsonUrl = "https://kfruti88.github.io/clay-county-news/news_data.json";
    const hubUrl = "https://supportmylocalcommunity.com/local-news/"; // Your Main Hub #lock

    const params = new URLSearchParams(window.location.search);
    const targetId = params.get('id');
    const path = window.location.href.toLowerCase();
    
    // Detect if we are on the SupportMyLocalCommunity Hub
    const isHub = path.includes('supportmylocalcommunity.com/local-news');

    const townColors = {
        "Flora": { bg: "#0c0b82", text: "#fe4f00" },
        "Louisville": { bg: "#010101", text: "#eb1c24" },
        "Clay City": { bg: "#0c30f0", text: "#8a8a88" },
        "Xenia": { bg: "#000000", text: "#fdb813" },
        "Sailor Springs": { bg: "#000000", text: "#a020f0" },
        "Clay County": { bg: "#333333", text: "#ffffff" }
    };

    fetch(jsonUrl)
        .then(res => res.json())
        .then(data => {
            // FILTER: Strictly Clay County Towns Only
            const clayTowns = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs", "Clay County"];
            const filteredData = data.filter(item => 
                item.tags.some(tag => clayTowns.includes(tag))
            );

            if (isHub) {
                // --- HUB MODE: RENDER ALL FULL STORIES ---
                filteredData.forEach(item => {
                    renderFullStoryInList(item);
                });

                // If a specific story was requested, scroll to it
                if (targetId) {
                    setTimeout(() => {
                        const element = document.getElementById(targetId);
                        if (element) {
                            element.scrollIntoView({ behavior: 'smooth' });
                            element.style.borderLeftWidth = "30px"; // Visual highlight
                        }
                    }, 500);
                }
            } else {
                // --- TOWN MODE: RENDER SUMMARIES ONLY ---
                let currentTown = "";
                if (path.includes('flora')) currentTown = "Flora";
                else if (path.includes('louisville')) currentTown = "Louisville";
                else if (path.includes('clay-city')) currentTown = "Clay City";
                else if (path.includes('xenia')) currentTown = "Xenia";
                else if (path.includes('sailor-springs')) currentTown = "Sailor Springs";

                const townNews = filteredData.filter(item => 
                    !currentTown || item.tags.includes(currentTown) || item.tags.includes("Clay County")
                );

                townNews.forEach(item => renderSummary(item));
            }
        });

    function renderSummary(item) {
        if (!summaryContainer) return;
        const mainBG = townColors[item.tags[0]]?.bg || "#333";
        summaryContainer.innerHTML += `
            <div class="summary-box" style="--town-color: ${mainBG}">
                <h3>${item.title}</h3>
                <p>${item.full_story.substring(0, 180)}...</p>
                <a href="${hubUrl}?id=${item.id}" class="read-more-btn">Read Full Story ↓</a>
            </div>`;
    }

    function renderFullStoryInList(item) {
        if (!fullContainer) return;
        const mainBG = townColors[item.tags[0]]?.bg || "#333";
        fullContainer.innerHTML += `
            <div id="${item.id}" class="full-story-display" style="--town-color: ${mainBG}">
                <h1>${item.title}</h1>
                <div class="story-body">${item.full_story}</div>
            </div>`;
    }
});
