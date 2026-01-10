document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    const jsonUrl = "https://kfruti88.github.io/clay-county-news/news_data.json";
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    const params = new URLSearchParams(window.location.search);
    const targetId = params.get('id');
    const path = window.location.href.toLowerCase();
    
    // Improved detection: Check if we are in the local-news folder or on the hub page
    const isHub = path.includes('/local-news') || !!fullContainer;

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
            // 1. MASTER FILTER: Strictly Clay County Towns
            const clayTownList = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"];
            
            const filteredData = data.filter(item => {
                const isClay = item.tags.some(tag => clayTownList.includes(tag) || tag === "Clay County");
                const isNotWayne = !item.title.includes("Cisne") && !item.title.includes("Wayne County");
                return isClay && isNotWayne;
            });

            if (isHub) {
                // --- HUB MODE: RENDER ALL FULL STORIES ---
                if (fullContainer) fullContainer.innerHTML = ''; // Clear "Syncing" message
                
                filteredData.forEach(item => {
                    renderFullStoryInList(item);
                });

                // Handle the jump to the specific article
                if (targetId) {
                    setTimeout(() => {
                        const element = document.getElementById(targetId);
                        if (element) {
                            element.scrollIntoView({ behavior: 'smooth' });
                            element.style.borderLeftWidth = "30px"; 
                        }
                    }, 800);
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

                if (summaryContainer) {
                    summaryContainer.innerHTML = ''; // Clear "Connecting" message
                    townNews.forEach(item => renderSummary(item));
                }
            }
        })
        .catch(err => console.error("News engine failed to load:", err));

    function renderSummary(item) {
        if (!summaryContainer) return;
        const mainBG = townColors[item.tags[0]]?.bg || "#333";
        
        // ADDED target="_blank" to the button below
        summaryContainer.innerHTML += `
            <div class="summary-box" style="--town-color: ${mainBG}">
                <h3>${item.title}</h3>
                <p>${item.full_story.substring(0, 180)}...</p>
                <a href="${hubUrl}?id=${item.id}" target="_blank" class="read-more-btn">Read Full Story ↓</a>
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
