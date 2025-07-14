function viewDailyDigest(e) {
  const email = Session.getActiveUser().getEmail();

  const response = UrlFetchApp.fetch("https://inbox-assistant-x5uk.onrender.com/daily_digest", {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ email: email })
  });

  const result = JSON.parse(response.getContentText());

  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("📬 Daily Digest Summary"));

  const section = CardService.newCardSection();

  // Total emails
  section.addWidget(CardService.newTextParagraph().setText(
    "You’ve received <b>" + result.total + "</b> emails since your last digest."
  ));

  // Label breakdown
  if (result.breakdown && Object.keys(result.breakdown).length > 0) {
    const breakdownLines = [];
    for (var label in result.breakdown) {
      breakdownLines.push(label + ": " + result.breakdown[label]);
    }
    section.addWidget(CardService.newTextParagraph().setText(
      "<b>Label Breakdown:</b><br>" + breakdownLines.join("<br>")
    ));
  }

  // Action items
  if (result.action_items && result.action_items.length > 0) {
    const actionList = result.action_items.map(function(item, i) {
      return (i + 1) + ". " + item;
    }).join("<br>");

    section.addWidget(CardService.newTextParagraph().setText(
      "<b>🧠 Action Items:</b><br>" + actionList
    ));
  } else {
    section.addWidget(CardService.newTextParagraph().setText("✅ No action items identified."));
  }

  card.addSection(section);
  return card.build();
}
