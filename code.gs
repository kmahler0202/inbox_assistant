function buildAddOn(e) {
  var card = CardService.newCardBuilder();
  var section = CardService.newCardSection();

  section.addWidget(CardService.newTextInput()
    .setFieldName("message")
    .setTitle("Ask GPT"));

  section.addWidget(CardService.newTextButton()
    .setText("Send")
    .setOnClickAction(
      CardService.newAction()
        .setFunctionName("handleChatSubmit")
    ));

  card.addSection(section);
  return card.build();
}

function handleChatSubmit(e) {
  var message = e.commonEventObject.formInputs.message.stringInputs.value[0];

  Logger.log("User said: " + message);
  return "This is a fake GPT reply to: " + message;
  // var userMessage = e.commonEventObject.formInputs.message.stringInputs.value[0];

  // var response = UrlFetchApp.fetch("https://inbox-assistant-x5uk.onrender.com", {
  //   method: "post",
  //   contentType: "application/json",
  //   payload: JSON.stringify({ message: userMessage })
  // });

  // var json = JSON.parse(response.getContentText());
  // var reply = json.reply;

  // var card = CardService.newCardBuilder();
  // var section = CardService.newCardSection();

  // section.addWidget(CardService.newTextParagraph().setText("<b>You:</b> " + userMessage));
  // section.addWidget(CardService.newTextParagraph().setText("<b>GPT:</b> " + reply));

  // card.addSection(section);
  // return card.build();
}

