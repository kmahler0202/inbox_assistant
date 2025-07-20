document.getElementById('digest').addEventListener('click', async () => {
  fetch("https://inbox-assistant-x5uk.onrender.com/daily_digest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "kmahler0202@gmail.com" })
  })
  .then(res => res.json())
  .then(data => alert(`Digest: ${data.total} emails sorted!`))
  .catch(err => alert("Error: " + err));
});

document.getElementById('followups').addEventListener('click', async () => {
  fetch("https://inbox-assistant-x5uk.onrender.com/get_followups")
  .then(res => res.json())
  .then(data => alert(`Follow-ups: ${data.length} emails`))
  .catch(err => alert("Error: " + err));
});
