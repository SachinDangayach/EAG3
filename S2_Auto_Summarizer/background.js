'use strict';

const DEFAULTS = { lastPercentage: 30 };

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get('summarizerState', ({ summarizerState }) => {
    if (!summarizerState) {
      chrome.storage.local.set({ summarizerState: DEFAULTS });
    }
  });
});
