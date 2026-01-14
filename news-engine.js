document.addEventListener('DOMContentLoaded', () => {
    const summaryContainer = document.getElementById('town-summaries');
    const fullContainer = document.getElementById('full-news-feed');
    
    const jsonUrl = "https://kfruti88.github.io/clay-county-news/news_data.json";
    const hubUrl = "https://supportmylocalcommunity.com/local-news/";

    // Apply the Blue Background you requested to the body
    document.body.style.backgroundColor = "#0c71c3";

    // DETECTION: If 'full-news-feed' exists, we are in Hub Mode (Local News Hub)
    const isHubMode = !!fullContainer;

    const townColors = {
        "Flora": { bg: "#0c0b82", text: "#fe4f00" },
        "Louisville": { bg: "#010101", text: "#eb1c24" },
        "Clay City": { bg: "#0c30f0", text: "#8a8a88" },
        "Xenia": { bg: "#000000", text: "#fdb813" },
        "Sailor Springs": { bg: "#000000", text: "#a020f0" },
        "Obituary": { bg: "#333333", text: "#ffffff" },
        "Fire Dept": { bg: "#ff4500", text: "#ffffff" },
        "Police/PD": { bg: "#00008b", text: "#ffffff" },
        "Clay County": { bg: "#333333", text: "#ffffff" }
    };

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
                // --- HUB MODE (Full Articles) ---
                fullContainer.innerHTML = ''; 
                filteredData.forEach(item => renderFullStory(item));
                handleScroll(); // Trigger the bookmark jump
            } else if (summaryContainer) {
                // --- SUMMARY MODE (Town Pages / Home) ---
                summaryContainer.innerHTML = ''; 
                
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
        .catch(err => console.error("News Load Error:", err));

    function renderSummary(item) {
        if (!summaryContainer) return;
        const mainBG = townColors[item.tags[0]]?.bg || "#333";
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:15px;">` : '';
        
        summaryContainer.innerHTML += `
            <div class="summary-box" style="--town-color: ${mainBG};">
                <h3>${item.title}</h3>
                <p style="font-size: 0.9rem; color: #555;">${item.date}</p>
                ${imgHTML}
                <p>${item.full_story.substring(0, 180)}...</p>
                <a href="${hubUrl}?id=${item.id}" class="read-more-btn">Read Full Story</a>
            </div>`;
    }

    function renderFullStory(item) {
        if (!fullContainer) return;
        const mainBG = townColors[item.tags[0]]?.bg || "#333";
        const imgHTML = item.image ? `<img src="${item.image}" style="width:100%; border-radius:12px; margin-bottom:20px;">` : '';

        fullContainer.innerHTML += `
            <article id="${item.id}" class="full-story-display" style="--town-color: ${mainBG}">
                <h1>${item.title}</h1>
                <p style="text-align: center; font-weight: bold; color: #666;">
                    ${item.date} | ${item.tags.join(' | ')}
                </p>
                ${imgHTML}
                <div class="story-body">${item.full_story}</div>
            </article>`;
    }

    function handleScroll() {
        const params = new URLSearchParams(window.location.search);
        const targetId = params.get('id');

        if (targetId) {
            let attempts = 0;
            const scrollInterval = setInterval(() => {
                const element = document.getElementById(targetId);
                attempts++;

                if (element) {
                    clearInterval(scrollInterval);
                    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    // Visual Flash/Highlight
                    element.style.boxShadow = "0 0 40px #ffff00"; 
                    setTimeout(() => { element.style.boxShadow = "0 8px 32px 0 rgba(0, 0, 0, 0.2)"; }, 3000);
                } else if (attempts > 60) {
                    clearInterval(scrollInterval);
                }
            }, 100);
        }
    }
});
