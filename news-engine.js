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
            // MASTER FILTER: Strictly Clay County Towns & Exclusion of Wayne County keywords
            const clayTownList = ["Flora", "Louisville", "Clay City", "Xenia", "Sailor Springs"];
            
            const filteredData = data.filter(item => {
                const isClay = item.tags.some(tag => clayTownList.includes(tag) || tag === "Clay County");
                const isNotWayne = !item.title.includes("Cisne") && !item.title.includes("Wayne County");
                return isClay && isNotWayne;
            });

            if (isHubMode) {
                // --- HUB MODE: RENDER ALL FULL STORIES ---
                fullContainer.innerHTML = ''; // Clear loading message
                filteredData.forEach(item => renderFullStory(item));

                // Handle the auto-scroll "jump" to a specific story ID
                const params = new URLSearchParams(window.location.search);
                const targetId = params.get('id');
                if (targetId) {
                    setTimeout(() => {
                        const element = document.getElementById(targetId);
                        if (element) {
                            element.scrollIntoView({ behavior: 'smooth' });
                            element.style.borderLeftWidth = "35px"; // Visual highlight
                        }
                    }, 1000); // 1 second delay to ensure page is fully painted
                }
            } else if (summaryContainer) {
                // --- TOWN/PORTAL MODE: RENDER SUMMARIES ONLY ---
                summaryContainer.innerHTML = ''; // Clear loading message
                
                // Detection for town-specific filtering based on URL path
                const path = window.location.href.toLowerCase();
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
        })
        .catch(err => console.error("Database connection failed:", err));

    function renderSummary(item) {
        if (!summaryContainer) return;
        const mainBG = townColors[item.tags[0]]?.bg || "#333";
        summaryContainer.innerHTML += `
            <div class="summary-box" style="--town-color: ${mainBG}">
                <h3>${item.title}</h3>
                <p>${item.full_story.substring(0, 160)}...</p>
                <a href="${hubUrl}?id=${item.id}" target="_blank" class="read-more-btn">Read Full Story</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const mainBG = townColors[item.tags[0]]?.bg || "#333";
        fullContainer.innerHTML += `
            <div id="${item.id}" class="full-story-display" style="--town-color: ${mainBG}; border-left: 15px solid ${mainBG}; margin-bottom: 30px; padding: 30px; background: #fff; border-radius: 12px; scroll-margin-top: 150px;">
                <h1 style="margin-top:0;">${item.title}</h1>
                <div class="story-body" style="white-space: pre-wrap; line-height: 1.8; font-size: 1.15rem;">${item.full_story}</div>
            </div>`;
    }
});
