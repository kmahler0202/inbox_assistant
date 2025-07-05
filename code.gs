function buildAddOn(e) {
  var card = CardService.newCardBuilder();
  
  var section = CardService.newCardSection()
    .addWidget(CardService.newTextParagraph().setText("Welcome to Inbox Assistant!"))
    .addWidget(
      CardService.newTextButton()
        .setText("Classify 10 Emails")
        .setOnClickAction(CardService.newAction().setFunctionName("classifyRecentEmails"))
    )
    .addWidget(
      CardService.newTextInput()
        .setFieldName("gptInput")
        .setTitle("Ask GPT")
    )
    .addWidget(
      CardService.newTextButton()
        .setText("Send")
        .setOnClickAction(CardService.newAction().setFunctionName("handleChatSubmit"))
    );

  card.addSection(section);
  return card.build();
}


function handleChatSubmit(value) {
  if (!value) value = "No message provided.";

  try {
    const payload = {
      message: value
    };

    const options = {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };

    const response = UrlFetchApp.fetch("https://inbox-assistant-x5uk.onrender.com/chat", options);
    const json = JSON.parse(response.getContentText());
    const reply = json.reply;

    // Addon environment compatibility: always return a card
    return CardService.newCardBuilder()
      .addSection(CardService.newCardSection()
        .addWidget(CardService.newTextParagraph().setText(reply)))
      .build();

  } catch (e) {
    return CardService.newCardBuilder()
      .addSection(CardService.newCardSection()
        .addWidget(CardService.newTextParagraph().setText("Error: " + e.message)))
      .build();
  }
}



