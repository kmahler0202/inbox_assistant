function addSummarizeButton() {
    if (document.querySelector('#summarize-thread')) return;

    const subjectLine = document.querySelector("h2.hP");
    if (!subjectLine) return;

    const button = document.createElement("button");
    button.innerText = "🧹 Summarize Thread";
    button.id = "summarize-thread";
    button.style.marginLeft = "10px";
    button.style.padding = "6px";
    button.style.cursor = "pointer";

    button.onclick = async () => {
        showSummary("⏳ Summarizing…");

        // Example API call (replace with your real endpoint)
        const response = await fetch("https://inbox-assistant-x5uk.onrender.com/summarize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                subject: subjectLine.innerText,
                body: getEmailBody(), 
                email: "kmahler0202@gmail.com"
            })
        });

        const data = await response.json();
        showSummary(`✅ ${data.summary}`);
    };

    subjectLine.parentNode.appendChild(button);
}

function showSummary(text) {
    let summaryBox = document.getElementById('mailman-summary-box');
    if (!summaryBox) {
        const subjectLine = document.querySelector("h2.hP");
        summaryBox = document.createElement("div");
        summaryBox.id = 'mailman-summary-box';
        summaryBox.style.marginTop = "12px";
        summaryBox.style.padding = "12px";
        summaryBox.style.backgroundColor = "#e8f0fe";
        summaryBox.style.borderRadius = "8px";
        summaryBox.style.fontSize = "14px";
        summaryBox.style.fontFamily = "Arial, sans-serif";
        summaryBox.style.maxWidth = "80%";
        subjectLine.parentNode.appendChild(summaryBox);
    }
    summaryBox.innerText = text;
}

function getEmailBody() {
    const emailBodies = document.querySelectorAll(".a3s");
    if (!emailBodies.length) return "";
    return emailBodies[emailBodies.length - 1].innerText.trim();
}


const observer = new MutationObserver(() => addSummarizeButton());
observer.observe(document.body, { childList: true, subtree: true });
