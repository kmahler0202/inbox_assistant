function summarize(subject, body) {
  const response = UrlFetchApp.fetch("https://inbox-assistant-x5uk.onrender.com/summarize", {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ subject: subject, body: body }),
  });

  const result = JSON.parse(response.getContentText());
  return result.summary;
}
