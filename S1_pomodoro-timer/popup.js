'use strict';

const PHASE_LABELS = {
  work: 'Focus Time',
  short_break: 'Short Break',
  long_break: 'Long Break'
};

const PHASE_COLORS = {
  work: '#e74c3c',
  short_break: '#27ae60',
  long_break: '#2980b9'
};

const R = 88;
const CIRCUMFERENCE = 2 * Math.PI * R;

let state = null;
let tickInterval = null;

const $ = (id) => document.getElementById(id);

document.addEventListener('DOMContentLoaded', () => {
  $('ringFill').style.strokeDasharray = CIRCUMFERENCE;

  loadState();

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes.timerState) {
      state = changes.timerState.newValue;
      render();
    }
  });

  $('startPauseBtn').addEventListener('click', onStartPause);
  $('resetBtn').addEventListener('click', () => send('reset'));
  $('skipBtn').addEventListener('click', () => send('skip'));
  $('settingsToggleBtn').addEventListener('click', toggleSettings);
  $('saveSettingsBtn').addEventListener('click', saveSettings);
});

function loadState() {
  chrome.storage.local.get('timerState', ({ timerState }) => {
    state = timerState;
    render();
  });
}

function onStartPause() {
  if (!state) return;
  send(state.status === 'running' ? 'pause' : 'start');
}

function send(action, extra = {}) {
  chrome.runtime.sendMessage({ action, ...extra });
}

function timeLeft() {
  if (!state) return 0;
  if (state.status === 'running' && state.startTime) {
    const elapsed = Math.floor((Date.now() - state.startTime) / 1000);
    return Math.max(0, state.totalDuration - elapsed);
  }
  return state.pausedTimeLeft ?? 0;
}

function phaseDuration(phase, settings) {
  if (!settings) return 25 * 60;
  const map = {
    work: settings.workDuration * 60,
    short_break: settings.shortBreakDuration * 60,
    long_break: settings.longBreakDuration * 60
  };
  return map[phase] ?? settings.workDuration * 60;
}

function render() {
  if (!state) return;

  const tl = timeLeft();
  const m = Math.floor(tl / 60);
  const s = tl % 60;

  $('timeDisplay').textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  $('phaseLabel').textContent = PHASE_LABELS[state.phase] || 'Focus Time';

  // Progress ring
  const total = phaseDuration(state.phase, state.settings);
  const ratio = total > 0 ? tl / total : 1;
  $('ringFill').style.strokeDashoffset = CIRCUMFERENCE * (1 - ratio);
  $('ringFill').style.stroke = PHASE_COLORS[state.phase] || '#e74c3c';

  // Phase buttons
  document.querySelectorAll('.phase-btn').forEach(btn => {
    const active = btn.dataset.phase === state.phase;
    btn.classList.toggle('active', active);
    btn.style.background = active ? (PHASE_COLORS[state.phase] || '#e74c3c') : '';
  });

  // Start/Pause button
  $('startPauseBtn').textContent = state.status === 'running' ? 'Pause' : 'Start';

  // Dots
  renderDots();

  // Session label
  $('sessionCount').textContent = `Session ${state.pomodorosCompleted + 1}`;

  // Settings inputs
  if (state.settings) {
    $('inputWork').value = state.settings.workDuration;
    $('inputShort').value = state.settings.shortBreakDuration;
    $('inputLong').value = state.settings.longBreakDuration;
  }

  // Tick interval for live countdown
  if (state.status === 'running') {
    if (!tickInterval) {
      tickInterval = setInterval(() => {
        const tl = timeLeft();
        const m = Math.floor(tl / 60);
        const s = tl % 60;
        $('timeDisplay').textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        const total = phaseDuration(state.phase, state.settings);
        $('ringFill').style.strokeDashoffset = CIRCUMFERENCE * (1 - tl / total);
      }, 1000);
    }
  } else {
    clearInterval(tickInterval);
    tickInterval = null;
  }
}

function renderDots() {
  const interval = state.settings?.longBreakInterval || 4;
  const completedInSet = state.pomodorosCompleted % interval;
  const container = $('dots');
  container.innerHTML = '';
  for (let i = 0; i < interval; i++) {
    const dot = document.createElement('div');
    dot.className = 'dot' + (i < completedInSet ? ' done' : '');
    container.appendChild(dot);
  }
}

function toggleSettings() {
  const panel = $('settingsPanel');
  const open = panel.classList.toggle('open');
  $('settingsToggleBtn').textContent = open ? '✕ Close' : '⚙ Settings';
}

function saveSettings() {
  const settings = {
    workDuration: Math.max(1, parseInt($('inputWork').value) || 25),
    shortBreakDuration: Math.max(1, parseInt($('inputShort').value) || 5),
    longBreakDuration: Math.max(1, parseInt($('inputLong').value) || 15)
  };
  send('updateSettings', { settings });
  toggleSettings();
}
