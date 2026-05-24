# Auto Summarizer — Chrome Extension

> Summarize any webpage in seconds. You choose how much.

A focused Chrome Extension (Manifest V3) powered by the **Gemini API** that condenses any webpage into a summary of your chosen length. Drag the slider to pick a percentage (10%–100%) and hit Summarize — the extension extracts the page text, calls Gemini, and displays the result right inside the popup.

---

## Features

| Feature | Description |
|---|---|
| **Percentage Slider** | Choose summary length from 10% (very brief) to 100% (near-full) — live label updates as you drag |
| **Gemini AI** | Uses `gemini-2.0-flash-lite` for fast, high-quality summarization |
| **Word Count Display** | Shows `~N words (X% of original)` so you know exactly what you got |
| **One-click Copy** | Copy the summary to clipboard with a single button |
| **Persistent Preference** | Your last-used percentage is saved and restored on next open |
| **Error Guidance** | Clear, actionable messages for invalid API keys, quota limits, or network issues |

---

## Project Structure

```
S2_Auto_Summarizer/
├── manifest.json          # Chrome Extension config (Manifest V3)
├── popup.html             # Extension popup UI
├── popup.js               # UI logic and Gemini API calls
├── styles.css             # Dark-themed popup styles
├── content.js             # Content script — extracts page text
├── background.js          # Service worker — persists user preferences
├── config.js              # Your API key (gitignored — you create this)
├── config.example.js      # Committed template showing the expected shape of config.js
├── .gitignore             # Excludes config.js from git
├── generate_icons.py      # Script to generate teal placeholder icons
└── icons/                 # Extension icons (16×16, 48×48, 128×128)
```

---

## Setup

### 1. Get a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in and create a new API key (free tier available)

### 2. Configure the API Key

```bash
cp config.example.js config.js
```

Open `config.js` and replace the placeholder with your real key:

```js
const GEMINI_API_KEY = 'your_real_api_key_here';
```

`config.js` is gitignored — your key will never be committed.

### 3. Generate Icons (optional — already included)

```bash
python3 generate_icons.py
```

### 4. Load in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Toggle on **Developer mode** (top-right)
3. Click **Load unpacked**
4. Select the `S2_Auto_Summarizer/` folder (the one containing `manifest.json`)
5. The Auto Summarizer icon appears in your toolbar — pin it for easy access

---

## Usage

1. Navigate to any webpage with text content
2. Click the Auto Summarizer icon in the toolbar
3. Drag the **Summary Length** slider to set the desired percentage
4. Click **Summarize**
5. Read the summary in the popup — click **Copy** to copy it

### Slider Guide

| Range | Result |
|---|---|
| 10–20% | Ultra-brief — key takeaway only |
| 25–40% | Concise summary — main points covered |
| 50–70% | Detailed summary — most context preserved |
| 80–100% | Near-full — light condensation |

---

## Tech Stack

- **JavaScript** (ES2020) — popup logic, content script, service worker
- **Gemini API** (`gemini-2.0-flash-lite`) — AI summarization
- **HTML5 / CSS3** — popup UI with dark theme and teal accent
- **Chrome Extension APIs** — `activeTab`, `scripting`, `storage`, `tabs`
- **Manifest V3** — latest Chrome Extension platform

---

## Security Notes

- Your API key lives only in `config.js` on your local machine
- `config.js` is gitignored — it is never committed to version control
- Page text is sent directly to the Gemini API; no third-party servers are involved
- Only the active tab's content is ever read, and only when you click Summarize

---

## License

Open source. Free to use, modify, and distribute.
