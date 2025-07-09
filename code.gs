function buildAddOn(e) {
  // Logo image
  const image = CardService.newImage()
    .setImageUrl("https://ssl.gstatic.com/docs/doclist/images/mediatype/icon_1_image_x32.png") // Replace this with your own hosted logo if you have one
    .setAltText("Inbox Assistant");

  // Friendly welcome message with enhanced feature list
  const welcomeText = CardService.newTextParagraph().setText(
    "<b>Welcome to Inbox Assistant!</b><br><br>" +
    "✨ <b>Automatically sort</b> your inbox – powered by AI<br>" +
    "📝 <b>Instantly summarize</b> long email threads<br>" +
    "📬 <b>Daily digests</b> of your inbox activity<br>" +
    "✅ <b>Extract action items</b> from important emails<br>" +
    "✍️ <b>Draft smart replies</b> (never sent without your OK!)<br>" +
    "⏰ <b>Follow-up tracker</b> – know when to reach back out<br>" +
    "🧠 <b>Chat with a GPT assistant</b> about your inbox<br>" +
    "⚙️ <b>Configure</b> exactly which features are active"
  );

  // Configure button
  const configureAction = CardService.newAction()
    .setFunctionName("showConfigPage");

  const configureButton = CardService.newTextButton()
    .setText("Configure")
    .setOnClickAction(configureAction)
    .setTextButtonStyle(CardService.TextButtonStyle.FILLED);

  // Layout
  const section = CardService.newCardSection()
    .addWidget(image)
    .addWidget(welcomeText)
    .addWidget(configureButton);

  // Build and return card
  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("Welcome"))
    .addSection(section)
    .build();

  return card;
}


function showConfigPage(e) {
  const sortingSection = CardService.newCardSection()
    .setHeader("📂 Inbox Sorting")
    .setCollapsible(true)
    .setNumUncollapsibleWidgets(0)  // makes it start collapsed

    .addWidget(
      CardService.newSelectionInput()
        .setType(CardService.SelectionInputType.CHECK_BOX)
        .setFieldName("autoSortEnabled")
        .addItem("Enable automatic inbox sorting", "enabled", false)
    )

    .addWidget(
      CardService.newSelectionInput()
        .setType(CardService.SelectionInputType.CHECK_BOX)
        .setTitle("Select labels to apply")
        .setFieldName("sortingLabels")
        .addItem("📁 Work", "Work", true)
        .addItem("🏠 Personal", "Personal", true)
        .addItem("🏷️ Promotions", "Promotions", false)
        .addItem("📬 Newsletters", "Newsletter", false)
    )

    .addWidget(
      CardService.newTextInput()
        .setFieldName("customLabels")
        .setTitle("Add custom labels (optional)")
        .setHint("Separate with commas: e.g. School, Family")
    );

  const summarizerSection = CardService.newCardSection()
    .setHeader("📝 Email Summarization")
    .setCollapsible(true)
    .setNumUncollapsibleWidgets(0)

    .addWidget(
      CardService.newSelectionInput()
        .setType(CardService.SelectionInputType.CHECK_BOX)
        .setFieldName("summarizerEnabled")
        .addItem("Enable email summarization feature", "enabled", false)
    );

  const saveAction = CardService.newAction().setFunctionName("saveSortingSettings");

  const saveButton = CardService.newTextButton()
    .setText("Save Settings")
    .setOnClickAction(saveAction)
    .setTextButtonStyle(CardService.TextButtonStyle.FILLED);

  const backButton = CardService.newTextButton()
    .setText("Back")
    .setOnClickAction(CardService.newAction().setFunctionName("buildAddOn"));

  const buttonSection = CardService.newCardSection()
    .addWidget(saveButton)
    .addWidget(backButton);

  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("Configure Inbox Assistant"))
    .addSection(sortingSection)
    .addSection(summarizerSection)
    .addSection(buttonSection)
    .build();

  return card;
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



