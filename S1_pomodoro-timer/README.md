# 🍅 Pomodoro Timer — Chrome Extension

> Stay focused. Work smarter. Rest better.

A clean, feature-rich Pomodoro Timer built as a **Google Chrome Extension** using Manifest V3. It helps you apply the [Pomodoro Technique](https://en.wikipedia.org/wiki/Pomodoro_Technique) to boost productivity and maintain a healthy work-rest balance.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Visual Progress Ring** | SVG-based circular timer shows remaining time at a glance |
| **Session Tracking** | Tracks completed Pomodoros; auto-suggests a Long Break after every 4 sessions |
| **Phase Switching** | Instantly switch between Pomodoro, Short Break, and Long Break modes |
| **Customizable Intervals** | Set your own durations for work, short break, and long break |
| **Background Execution** | Uses Chrome's Alarm API — timer keeps running even when the popup is closed |
| **System Notifications** | Get alerted when it's time to switch phases |
| **Persistent State** | All timer state and settings survive popup close/reopen via `chrome.storage.local` |

---

## 🗂️ Project Structure

```
S1_pomodoro-timer/
├── manifest.json        # Chrome Extension config (Manifest V3)
├── background.js        # Service worker — alarms, state, notifications
├── popup.html           # Extension UI markup
├── popup.js             # UI logic, button handlers, background messaging
├── styles.css           # Popup styles including the SVG progress ring
├── icons/               # Extension icons (16×16 to 128×128)
└── generate_icons.py    # Script to generate placeholder icons
```

---

## 🚀 Installation

1. **Clone or download** this repository:
   ```bash
   git clone <repository-url>
   ```

2. Open **Google Chrome** and go to:
   ```
   chrome://extensions/
   ```

3. Toggle on **Developer mode** (top-right corner).

4. Click **Load unpacked**.

5. Select the `S1_pomodoro-timer/` directory (the folder containing `manifest.json`).

6. The Pomodoro Timer icon will appear in your Chrome toolbar. Pin it for easy access.

---

## 🎮 Usage

Click the extension icon in your toolbar to open the timer.

### Controls

| Button | Action |
|---|---|
| **Start** | Begin the current phase countdown |
| **Pause** | Temporarily halt the timer |
| **Reset** | Restart the current phase from the beginning |
| **Skip** | Jump to the next phase immediately |
| **⚙ Settings** | Open the settings panel to adjust durations |

### Default Intervals

| Phase | Duration |
|---|---|
| Pomodoro (Focus) | 25 minutes |
| Short Break | 5 minutes |
| Long Break | 15 minutes |
| Sessions before Long Break | 4 |

### Settings

Click **⚙ Settings** to customize each interval (in minutes). Hit **Save & Reset** to apply changes — the timer restarts with the new durations.

---

## 🛠️ Tech Stack

- **JavaScript** (ES6+) — background service worker and popup logic
- **HTML5 / CSS3** — popup UI with SVG progress ring animation
- **Chrome Extension APIs** — `chrome.alarms`, `chrome.storage`, `chrome.notifications`
- **Manifest V3** — latest Chrome Extension platform

---

## 📋 How the Pomodoro Technique Works

1. Choose a task to work on.
2. Set the timer for **25 minutes** and focus exclusively on the task.
3. When the timer rings, take a **5-minute short break**.
4. After **4 Pomodoros**, reward yourself with a **15-minute long break**.
5. Repeat.

---

## 📄 License

This project is open source. Feel free to use, modify, and distribute it.
