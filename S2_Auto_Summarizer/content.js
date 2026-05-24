'use strict';

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action !== 'extractText') return;

  let raw = document.body?.innerText || document.documentElement.innerText || '';

  // Collapse runs of whitespace/blank lines to single newlines
  const text = raw
    .replace(/\r\n/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();

  const wordCount = text.split(/\s+/).filter(Boolean).length;

  sendResponse({ text, wordCount });
  return true;
});
