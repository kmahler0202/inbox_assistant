function buildAddOn(e) {
  const email = Session.getActiveUser().getEmail(); // might return service account

  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ email: email })
  };

  const response = UrlFetchApp.fetch(
    "https://inbox-assistant-x5uk.onrender.com/is_onboarded",
    options
  );

  const onboarded = JSON.parse(response.getContentText()).onboarded;

  return onboarded ? buildHomePage(e) : buildWelcomePage(e);
}

function buildHomePage(e) {
  // Section 1: Quick Summary
  var email = Session.getActiveUser().getEmail();
  var response = UrlFetchApp.fetch("https://inbox-assistant-x5uk.onrender.com/get_stats", {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify({email: email})
  });

  var stats = JSON.parse(response.getContentText());

  const summary = buildInboxOverviewCard(stats);

  // Section 2: Actions
  const viewDigestBtn = CardService.newTextButton()
    .setText("View Daily Digest")
    .setOnClickAction(CardService.newAction().setFunctionName("viewDailyDigest"));

  const summarizeBtn = CardService.newTextButton()
    .setText("Summarize Current Thread")
    .setOnClickAction(CardService.newAction().setFunctionName("fetchEmailSummary"));

  const actionsSection = CardService.newCardSection()
    .addWidget(summary)
    .addWidget(viewDigestBtn)
    .addWidget(summarizeBtn);

  // Section 3: Assistant Input
  const chatInput = CardService.newTextInput()
    .setFieldName("chatMessage")
    .setHint("Ask anything about your email...");

  const chatButton = CardService.newTextButton()
    .setText("Send to Assistant")
    .setOnClickAction(CardService.newAction().setFunctionName("handleChatSubmit"));

  const chatSection = CardService.newCardSection()
    .setHeader("💬 Talk to GPT Assistant")
    .addWidget(chatInput)
    .addWidget(chatButton);

  // Section 4: Feature Shortcuts
  const shortcutSection = CardService.newCardSection()
    .setHeader("⚡ Quick Access")
    .addWidget(
      CardService.newTextButton()
        .setText("✍️ Draft Smart Reply")
        .setOnClickAction(CardService.newAction().setFunctionName("generateDraftReply"))
    )
    .addWidget(
      CardService.newTextButton()
        .setText("📌 Extract Action Items")
        .setOnClickAction(CardService.newAction().setFunctionName("extractActionItems"))
    )
    .addWidget(
      CardService.newTextButton()
        .setText("⏰ View Follow-Ups")
        .setOnClickAction(CardService.newAction().setFunctionName("viewFollowUps"))
    )
    .addWidget(
      CardService.newTextButton()
        .setText("⚙️ Configure Settings")
        .setOnClickAction(CardService.newAction().setFunctionName("showConfigPage"))
    );

  // Combine everything
  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("Inbox Assistant"))
    .addSection(actionsSection)
    .addSection(chatSection)
    .addSection(shortcutSection)
    .build();

  return card;
}

function buildWelcomePage(e) {
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
  const email = Session.getActiveUser().getEmail();

  // Fetch saved settings from backend
  const response = UrlFetchApp.fetch("https://inbox-assistant-x5uk.onrender.com/get_settings", {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ email: email })
  });

  const settings = JSON.parse(response.getContentText());

  var labels = [];
  try {
    if (typeof settings.sortingLabels === "string") {
      labels = JSON.parse(settings.sortingLabels);
    } else if (Array.isArray(settings.sortingLabels)) {
      labels = settings.sortingLabels;
    }
  } catch (e) {
    labels = [];
  }

const sortingSection = CardService.newCardSection()
  .setHeader("📂 Inbox Sorting")
  .setCollapsible(true)
  .setNumUncollapsibleWidgets(0)
  .addWidget(
    CardService.newSelectionInput()
      .setType(CardService.SelectionInputType.CHECK_BOX)
      .setFieldName("autoSortEnabled")
      .addItem("Enable automatic inbox sorting", "enabled", isChecked(settings.autoSortEnabled))
  )
  .addWidget(
    CardService.newSelectionInput()
      .setType(CardService.SelectionInputType.CHECK_BOX)
      .setTitle("Select labels to apply")
      .setFieldName("sortingLabels")
      .addItem("📁 Work", "Work", labels.indexOf("Work") !== -1)
      .addItem("🏠 Personal", "Personal", labels.indexOf("Personal") !== -1)
      .addItem("🏷️ Promotions", "Promotions", labels.indexOf("Promotions") !== -1)
      .addItem("📬 Newsletters", "Newsletter", labels.indexOf("Newsletter") !== -1)
  )
  .addWidget(
    CardService.newTextInput()
      .setFieldName("customLabels")
      .setTitle("Add custom labels (optional)")
      .setValue("")
      .setHint("Separate with commas: e.g. School, Family")
  );

  // 📝 Summarizer Section
  const summarizerSection = CardService.newCardSection()
    .setHeader("📝 Email Summarization")
    .setCollapsible(true)
    .setNumUncollapsibleWidgets(0)
    .addWidget(
      CardService.newSelectionInput()
        .setType(CardService.SelectionInputType.CHECK_BOX)
        .setFieldName("summarizerEnabled")
        .addItem("Enable email summarization feature", "enabled", isChecked(settings.summarizerEnabled))
    );

  // 🕒 Daily Digest Section
  const digestSection = CardService.newCardSection()
    .setHeader("🕒 Daily Digest")
    .setCollapsible(true)
    .setNumUncollapsibleWidgets(0)
    .addWidget(
      CardService.newSelectionInput()
        .setType(CardService.SelectionInputType.CHECK_BOX)
        .setFieldName("digestEnabled")
        .addItem("Enable daily email digests", "enabled", isChecked(settings.digestEnabled))
    )
    .addWidget(
      CardService.newSelectionInput()
        .setType(CardService.SelectionInputType.DROPDOWN)
        .setTitle("Delivery time")
        .setFieldName("digestTime")
        .addItem("8:00 AM", "08:00", settings.digestTime === "08:00")
        .addItem("12:00 PM", "12:00", settings.digestTime === "12:00")
        .addItem("6:00 PM", "18:00", settings.digestTime === "18:00")
    );

  // 📌 Action Items Section
  const actionItemSection = CardService.newCardSection()
    .setHeader("📌 Extract Action Items")
    .setCollapsible(true)
    .setNumUncollapsibleWidgets(0)
    .addWidget(
      CardService.newSelectionInput()
        .setType(CardService.SelectionInputType.CHECK_BOX)
        .setFieldName("actionItemsEnabled")
        .addItem("Enable action item detection in emails", "enabled", isChecked(settings.actionItemsEnabled))
    );

  // ✍️ Draft Replies Section
  const draftReplySection = CardService.newCardSection()
    .setHeader("✍️ Draft Smart Replies")
    .setCollapsible(true)
    .setNumUncollapsibleWidgets(0)
    .addWidget(
      CardService.newSelectionInput()
        .setType(CardService.SelectionInputType.CHECK_BOX)
        .setFieldName("draftRepliesEnabled")
        .addItem("Enable smart draft replies", "enabled", isChecked(settings.draftRepliesEnabled))
    );

  // ⏰ Follow-Up Tracker Section
  const followUpSection = CardService.newCardSection()
    .setHeader("⏰ Follow-Up Tracker")
    .setCollapsible(true)
    .setNumUncollapsibleWidgets(0)
    .addWidget(
      CardService.newSelectionInput()
        .setType(CardService.SelectionInputType.CHECK_BOX)
        .setFieldName("followUpEnabled")
        .addItem("Enable follow-up reminders", "enabled", isChecked(settings.followUpEnabled))
    );

  // 💬 Chat Assistant Section
  const chatAssistantSection = CardService.newCardSection()
    .setHeader("💬 GPT Chat Assistant")
    .setCollapsible(true)
    .setNumUncollapsibleWidgets(0)
    .addWidget(
      CardService.newSelectionInput()
        .setType(CardService.SelectionInputType.CHECK_BOX)
        .setFieldName("chatAssistantEnabled")
        .addItem("Enable GPT chat inside inbox", "enabled", isChecked(settings.chatAssistantEnabled))
    );

  // ✅ Save + Back Buttons
  const saveAction = CardService.newAction().setFunctionName("saveSortingSettings");

  const saveButton = CardService.newTextButton()
    .setText("Save Settings")
    .setOnClickAction(saveAction)
    .setTextButtonStyle(CardService.TextButtonStyle.FILLED);

  const backButton = CardService.newTextButton()
    .setText("Back")
    .setOnClickAction(CardService.newAction().setFunctionName("buildHomePage"));

  const buttonSection = CardService.newCardSection()
    .addWidget(saveButton)
    .addWidget(backButton);

  return CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("Configure Inbox Assistant"))
    .addSection(sortingSection)
    .addSection(summarizerSection)
    .addSection(digestSection)
    .addSection(actionItemSection)
    .addSection(draftReplySection)
    .addSection(followUpSection)
    .addSection(chatAssistantSection)
    .addSection(buttonSection)
    .build();
}



function saveSortingSettings(e) {
  
  var email = Session.getActiveUser().getEmail();
  var form = e.formInput;

  form.email = email

  // Send to Flask backend
  UrlFetchApp.fetch("https://inbox-assistant-x5uk.onrender.com/save_settings", {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(form)
  });

  // Return to home page or show a confirmation card
  return CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle("Settings Saved"))
    .addSection(
      CardService.newCardSection().addWidget(
        CardService.newTextParagraph().setText("✅ Your preferences have been saved.")
      )
    )
    .addSection(
      CardService.newCardSection().addWidget(
        CardService.newTextButton()
          .setText("Return Home")
          .setOnClickAction(CardService.newAction().setFunctionName("buildHomePage"))
      )
    )
    .build();
}

function buildInboxOverviewCard(stats) {
  return CardService.newTextParagraph().setText(
    "<b>📬 Inbox Overview</b><br>" +
    "You’ve received <b>" + stats.emailsReceived + "</b> emails today.<br>" +
    "✅ <b>" + stats.emailsSorted + "</b> sorted automatically<br>" +
    "📝 <b>" + stats.summariesGenerated + "</b> summaries available<br>" +
    "📌 <b>" + stats.actionItemsExtracted + "</b> action ites extracted"
  );
}

function isChecked(field) {
  return (
    field &&
    field.stringInputs &&
    field.stringInputs.value &&
    field.stringInputs.value[0] === "enabled"
  );
}

function getList(field) {
  return (
    field &&
    field.stringInputs &&
    field.stringInputs.value
  ) || [];
}

function getSingleValue(field) {
  return (
    field &&
    field.stringInputs &&
    field.stringInputs.value &&
    field.stringInputs.value[0]
  ) || null;
}

function getListFromStringInput(field) {
  var raw = "";
  if (
    field &&
    field.stringInputs &&
    field.stringInputs.value &&
    field.stringInputs.value[0]
  ) {
    raw = field.stringInputs.value[0];
  }

  return raw
    .split(",")
    .map(function (s) {
      return s.trim();
    })
    .filter(function (s) {
      return s;
    });
}

function isChecked(val) {
  return val === true || val === "true";
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



