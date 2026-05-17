const DEFAULTS = {
  phase: 'work',
  status: 'idle',
  startTime: null,
  pausedTimeLeft: 25 * 60,
  totalDuration: 25 * 60,
  pomodorosCompleted: 0,
  settings: {
    workDuration: 25,
    shortBreakDuration: 5,
    longBreakDuration: 15,
    longBreakInterval: 4
  }
};

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get('timerState', ({ timerState }) => {
    if (!timerState) {
      chrome.storage.local.set({ timerState: DEFAULTS });
    }
  });
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name !== 'timerEnd') return;
  chrome.storage.local.get('timerState', ({ timerState }) => {
    if (timerState?.status === 'running') {
      handlePhaseComplete(timerState);
    }
  });
});

function handlePhaseComplete(state) {
  const { settings } = state;
  let newPhase, newDuration;
  let pomodorosCompleted = state.pomodorosCompleted;
  let notifTitle, notifMsg;

  if (state.phase === 'work') {
    pomodorosCompleted++;
    if (pomodorosCompleted % settings.longBreakInterval === 0) {
      newPhase = 'long_break';
      newDuration = settings.longBreakDuration * 60;
      notifTitle = 'Pomodoro Complete!';
      notifMsg = 'Time for a long break. You earned it!';
    } else {
      newPhase = 'short_break';
      newDuration = settings.shortBreakDuration * 60;
      notifTitle = 'Pomodoro Complete!';
      notifMsg = 'Take a short break.';
    }
  } else {
    newPhase = 'work';
    newDuration = settings.workDuration * 60;
    notifTitle = 'Break Over!';
    notifMsg = "Time to focus!";
  }

  chrome.storage.local.set({
    timerState: {
      ...state,
      phase: newPhase,
      status: 'idle',
      startTime: null,
      pausedTimeLeft: newDuration,
      totalDuration: newDuration,
      pomodorosCompleted
    }
  });

  chrome.notifications.create('phase_end_' + Date.now(), {
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: notifTitle,
    message: notifMsg
  });
}

function getPhaseDuration(phase, settings) {
  const map = {
    work: settings.workDuration * 60,
    short_break: settings.shortBreakDuration * 60,
    long_break: settings.longBreakDuration * 60
  };
  return map[phase] ?? settings.workDuration * 60;
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  chrome.storage.local.get('timerState', ({ timerState }) => {
    if (!timerState) {
      sendResponse({ success: false, error: 'No state' });
      return;
    }

    let newState = { ...timerState };

    switch (msg.action) {
      case 'start': {
        const timeLeft = timerState.pausedTimeLeft;
        chrome.alarms.create('timerEnd', { delayInMinutes: timeLeft / 60 });
        newState.status = 'running';
        newState.startTime = Date.now();
        newState.totalDuration = timeLeft;
        break;
      }

      case 'pause': {
        const elapsed = Math.floor((Date.now() - timerState.startTime) / 1000);
        const remaining = Math.max(0, timerState.totalDuration - elapsed);
        chrome.alarms.clear('timerEnd');
        newState.status = 'paused';
        newState.startTime = null;
        newState.pausedTimeLeft = remaining;
        break;
      }

      case 'reset': {
        chrome.alarms.clear('timerEnd');
        const duration = getPhaseDuration(timerState.phase, timerState.settings);
        newState.status = 'idle';
        newState.startTime = null;
        newState.pausedTimeLeft = duration;
        newState.totalDuration = duration;
        break;
      }

      case 'skip': {
        chrome.alarms.clear('timerEnd');
        handlePhaseComplete({ ...timerState });
        sendResponse({ success: true });
        return;
      }

      case 'updateSettings': {
        chrome.alarms.clear('timerEnd');
        const newSettings = { ...timerState.settings, ...msg.settings };
        const dur = getPhaseDuration(timerState.phase, newSettings);
        newState.settings = newSettings;
        newState.status = 'idle';
        newState.startTime = null;
        newState.pausedTimeLeft = dur;
        newState.totalDuration = dur;
        break;
      }

      default:
        sendResponse({ success: false, error: 'Unknown action' });
        return;
    }

    chrome.storage.local.set({ timerState: newState }, () => {
      sendResponse({ success: true });
    });
  });

  return true;
});
