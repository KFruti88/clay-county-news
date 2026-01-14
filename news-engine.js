document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    const jsonUrl = "https://kfruti88.github.io/clay-county-news/news_data.json";
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // DETECTION: If 'full-news-feed' exists, we are in Hub Mode showing full articles.
    const isHubMode = !!fullContainer;

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
            // MASTER FILTER: Clay County Towns
            const clayTownList = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"];
            
            const filteredData = data.filter(item => {
                // Keep it if it's one of our towns OR if it's a primary source (WNOI)
                const isClay = item.tags.some(tag => clayTownList.includes(tag) || tag === "Clay County");
                const isPrimary = item.is_primary === true;
                const isNotWayne = !item.title.includes("Cisne") && !item.title.includes("Wayne County");
                
                return (isClay || isPrimary) && isNotWayne;
            });

            if (isHubMode) {
                // --- HUB MODE: RENDER ALL FULL STORIES ---
                fullContainer.innerHTML = ''; 
                // This 'forEach' makes sure EVERY filtered article shows up
                filteredData.forEach(item => renderFullStory(item));

                // Handle auto-scroll logic
                const params = new URLSearchParams(window.location.search);
                const targetId = params.get('id') || window.location.hash.substring(1);
                if (targetId) {
                    setTimeout(() => {
                        const element = document.getElementById(targetId);
                        if (element) {
                            element.scrollIntoView({ behavior: 'smooth' });
                            element.style.borderLeftWidth = "35px"; 
                        }
                    }, 800);
                }
            } else if (summaryContainer) {
                // --- TOWN/PORTAL MODE: RENDER SUMMARIES ONLY ---
                summaryContainer.innerHTML = ''; 
                
                const path = window.location.href.toLowerCase();
                let currentTown = "";
                if (path.includes('flora')) currentTown = "Flora";
                else if (path.includes('louisville')) currentTown = "Louisville";
                else if (path.includes('clay-city')) currentTown = "Clay City";
                else if (path.includes('xenia')) currentTown = "Xenia";
                else if (path.includes('sailor-springs')) currentTown = "Sailor Springs";

                // Filter for the specific town page we are on
                const townNews = filteredData.filter(item => 
                    !currentTown || item.tags.includes(currentTown) || item.tags.includes("Clay County")
                );

                townNews.forEach(item => renderSummary(item));
            }
        })
        .catch(err => console.error("Database connection failed:", err));

    function renderSummary(item) {
        if (!summaryContainer) return;
        const mainBG = townColors[item.tags[0]]?.bg || "#333";
        // Using innerHTML += ensures it appends the next story instead of replacing the last one
        summaryContainer.innerHTML += `
            <div class="summary-box" style="--town-color: ${mainBG}; border-left: 10px solid ${mainBG}; margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-radius: 8px;">
                <h3 style="margin-top:0;">${item.title}</h3>
                <p style="font-size: 0.9rem; color: #555;">${item.date}</p>
                <p>${item.full_story.substring(0, 160)}...</p>
                <a href="${hubUrl}?id=${item.id}" target="_blank" class="read-more-btn" style="color: ${mainBG}; font-weight: bold;">Read Full Story</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const mainBG = townColors[item.tags[0]]?.bg || "#333";
        fullContainer.innerHTML += `
            <div id="${item.id}" class="full-story-display" style="--town-color: ${mainBG}; border-left: 15px solid ${mainBG}; margin-bottom: 30px; padding: 30px; background: #fff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); scroll-margin-top: 100px;">
                <h1 style="margin-top:0;">${item.title}</h1>
                <p style="color: #666; font-weight: bold;">${item.date} | Tags: ${item.tags.join(', ')}</p>
                <div class="story-body" style="white-space: pre-wrap; line-height: 1.8; font-size: 1.1rem; color: #333;">${item.full_story}</div>
            </div>`;
    }
});
