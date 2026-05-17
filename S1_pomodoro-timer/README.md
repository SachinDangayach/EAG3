# Pomodoro Timer Chrome Extension

A simple and elegant Pomodoro Timer built as a Google Chrome Extension. It helps you stay focused and manage your time effectively using the Pomodoro Technique.

## Features

- **Customizable Intervals**: Set your preferred durations for Focus Time, Short Breaks, and Long Breaks.
- **Visual Progress Ring**: A clean SVG-based progress ring shows how much time is left in the current phase.
- **Session Tracking**: Keeps track of how many Pomodoro sessions you have completed. Automatically suggests a Long Break after a set number of sessions (default is 4).
- **Background Execution**: Uses Chrome's Alarm API to keep track of time reliably even when the extension popup is closed.
- **Notifications**: Alerts you with a system notification when it's time to take a break or get back to work.
- **Persistent State**: Your timer's state and settings are saved automatically using `chrome.storage.local`, so you can close and reopen the extension without losing progress.

## Installation

1. Clone or download this repository.
2. Open Google Chrome and navigate to `chrome://extensions/`.
3. Enable **Developer mode** by toggling the switch in the top right corner.
4. Click on **Load unpacked**.
5. Select the directory containing the `manifest.json` file.

## Usage

- Click on the extension icon in your Chrome toolbar to open the timer.
- Click **Start** to begin the focus timer.
- Click **Pause** to temporarily stop the timer.
- Click **Reset** to restart the current phase.
- Click **Skip** to instantly complete the current phase and move to the next one.
- Click **⚙ Settings** to adjust the duration for Work, Short Break, and Long Break intervals.

## Project Structure

- `manifest.json`: Configuration file for the Chrome extension (Manifest V3).
- `background.js`: Service worker that manages alarms, timer state, and notifications in the background.
- `popup.html`: The HTML structure for the extension's user interface.
- `popup.js`: The frontend logic that handles UI updates, button clicks, and communication with the background script.
- `styles.css`: Styles for the popup interface, including the progress ring.
- `icons/`: Directory containing the extension icons in various sizes.
- `generate_icons.py`: A Python script used to generate placeholder icons.
