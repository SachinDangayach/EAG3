'use strict';

const GEMINI_ENDPOINT =
  `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`;

const $ = (id) => document.getElementById(id);

let currentTab = null;

document.addEventListener('DOMContentLoaded', async () => {
  await initTab();
  await loadSavedPercentage();
  bindEvents();
});

async function initTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTab = tab;
  $('pageTitle').textContent = tab.title || tab.url || 'Unknown page';
}

async function loadSavedPercentage() {
  const { summarizerState } = await chrome.storage.local.get('summarizerState');
  const pct = summarizerState?.lastPercentage ?? 30;
  $('lengthSlider').value = pct;
  updateSliderLabel(pct);
}

function bindEvents() {
  $('lengthSlider').addEventListener('input', () => {
    const pct = parseInt($('lengthSlider').value);
    updateSliderLabel(pct);
  });

  $('summarizeBtn').addEventListener('click', onSummarize);
  $('copyBtn').addEventListener('click', onCopy);
}

function updateSliderLabel(pct) {
  $('sliderValue').textContent = `${pct}%`;
}

async function onSummarize() {
  const pct = parseInt($('lengthSlider').value);

  setLoading(true);
  showError('');
  hideOutput();

  await chrome.storage.local.set({ summarizerState: { lastPercentage: pct } });

  let pageText, originalWordCount;
  try {
    const result = await extractPageText();
    pageText = result.text;
    originalWordCount = result.wordCount;
  } catch (err) {
    setLoading(false);
    showError('Could not read page content. Try reloading the page and try again.');
    return;
  }

  if (!pageText || pageText.length < 50) {
    setLoading(false);
    showError('Not enough text content found on this page to summarize.');
    return;
  }

  const targetWords = Math.max(30, Math.round((originalWordCount * pct) / 100));

  try {
    const summary = await callGemini(pageText, pct, targetWords, currentTab?.title || '');
    setLoading(false);
    showOutput(summary, originalWordCount, targetWords, pct);
  } catch (err) {
    setLoading(false);
    showError(formatApiError(err));
  }
}

function extractPageText() {
  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(
      currentTab.id,
      { action: 'extractText' },
      (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        if (!response) {
          reject(new Error('No response from content script'));
          return;
        }
        resolve(response);
      }
    );
  });
}

async function callGemini(pageText, pct, targetWords, pageTitle) {
  const prompt =
    `Summarize the following webpage content to approximately ${pct}% of its original length (about ${targetWords} words). ` +
    `Capture all key points and main ideas. Write in clear, concise prose.\n\n` +
    `Page title: ${pageTitle}\n\n` +
    `Content:\n${pageText.slice(0, 30000)}`;

  const response = await fetch(GEMINI_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { temperature: 0.4, maxOutputTokens: 2048 }
    })
  });

  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    const msg = errBody?.error?.message || `HTTP ${response.status}`;
    throw new Error(msg);
  }

  const data = await response.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) throw new Error('Empty response from Gemini API.');
  return text.trim();
}

function formatApiError(err) {
  const msg = err.message || String(err);
  if (msg.includes('API_KEY_INVALID') || msg.includes('DUMMY_API_KEY')) {
    return 'Invalid API key. Open config.js and replace DUMMY_API_KEY_REPLACE_ME with your real Gemini API key.';
  }
  if (msg.includes('RESOURCE_EXHAUSTED')) {
    return 'Gemini API quota exceeded. Please try again later.';
  }
  if (msg.includes('Failed to fetch')) {
    return 'Network error. Check your internet connection and try again.';
  }
  return `Gemini API error: ${msg}`;
}

function setLoading(loading) {
  $('summarizeBtn').disabled = loading;
  $('btnText').textContent = loading ? 'Summarizing…' : 'Summarize';
  $('spinner').classList.toggle('hidden', !loading);
}

function showOutput(summary, originalWords, targetWords, pct) {
  const summaryWords = summary.split(/\s+/).filter(Boolean).length;
  $('outputText').textContent = summary;
  $('wordCount').textContent = `~${summaryWords} words  (${pct}% of ${originalWords})`;
  $('outputSection').classList.remove('hidden');

  const copyBtn = $('copyBtn');
  copyBtn.textContent = 'Copy';
  copyBtn.classList.remove('copied');
}

function hideOutput() {
  $('outputSection').classList.add('hidden');
}

function showError(msg) {
  const el = $('errorMsg');
  if (msg) {
    el.textContent = msg;
    el.classList.remove('hidden');
  } else {
    el.classList.add('hidden');
  }
}

async function onCopy() {
  const text = $('outputText').textContent;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    const btn = $('copyBtn');
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = 'Copy';
      btn.classList.remove('copied');
    }, 2000);
  } catch {
    showError('Could not copy to clipboard.');
  }
}
