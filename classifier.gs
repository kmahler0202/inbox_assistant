function classifyRecentEmails() {
  var threads = GmailApp.getInboxThreads(0, 30);
  threads.forEach(function(thread) {
    var message = thread.getMessages()[0];
    var subject = message.getSubject();
    var body = message.getPlainBody().substring(0, 500);

    Logger.log('subject:' + subject);

    classifyEmail(thread, subject, body);

  });
}

function classifyEmail(thread, subject, snippet) {
  var payload = {
    subject: subject,
    snippet: snippet
  };

  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload)
  };

  var response = UrlFetchApp.fetch("https://inbox-assistant-x5uk.onrender.com/classify", options);
  var labelName = JSON.parse(response.getContentText()).label.trim();

  Logger.log("Assigned Label: " + labelName);

  var categoryMap = {
    "Promotions": "CATEGORY_PROMOTIONS",
    "Social": "CATEGORY_SOCIAL",
    "Updates": "CATEGORY_UPDATES",
    "Forums": "CATEGORY_FORUMS",
    "Personal": "CATEGORY_PERSONAL"
  };

  if (categoryMap[labelName]) {
    // FIND OUT LATER IF WE ARE ASSIGNING SAME GMAIL CATEGORY AS THE GMAIL CLASSIFIER IS
    Logger.log("🔒 Cannot assign Gmail category: " + labelName + " – skipping label.");
    return; // 🚫 Don't apply anything manually for categories
  } else {
    assignOrCreateLabel(thread, labelName);
  }
}

function assignCategory(thread, categoryId) {
  var categoryLabel = GmailApp.getUserLabelByName(categoryId);
  if (categoryLabel) {
    Logger.log("Applying system category: " + categoryId);
    thread.addLabel(categoryLabel);
  } else {
    Logger.log("❌ System category not found: " + categoryId);
  }
}

function assignOrCreateLabel(thread, labelName) {
  var label = null;
  var labels = GmailApp.getUserLabels();

  for (var i = 0; i < labels.length; i++) {
    if (labels[i].getName() === labelName) {
      label = labels[i];
      break;
    }
  }

  if (!label) {
    Logger.log("Creating new custom label: " + labelName);
    label = GmailApp.createLabel(labelName);
  } else {
    Logger.log("Found existing custom label: " + labelName);
  }

  thread.addLabel(label);
  Logger.log("✅ Applied custom label: " + labelName);
}



