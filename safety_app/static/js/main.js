/**
 * RESQ — Emergency & Rapid Response
 * Main App Utilities, Dynamic Safety Tips, Accessibility Engine, Audio Synthesis
 */

// CSRF Token Helper
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const csrftoken = getCookie('csrftoken');

// ==========================================================================
// Dynamic Safety Tip Rotator Engine
// ==========================================================================
const SafetyTips = {
  tips: [
    "Stay aware of your surroundings and keep your emergency contacts updated.",
    "Walking late? Use Campus SafeRide or walk along lit campus blue-light paths.",
    "In a medical emergency, keep the patient calm and stay with them until EMTs arrive.",
    "Save the 24/7 Campus Security Hotline to your phone's ICE favorites.",
    "Report suspicious activity early — campus dispatch is active 24 hours a day.",
    "Know your nearest emergency exit routes and fire pull stations in your hall."
  ],
  currentIndex: 0,
  timer: null,

  init() {
    const tipText = document.getElementById('resq-safety-tip-text');
    if (!tipText) return;

    this.timer = setInterval(() => {
      this.currentIndex = (this.currentIndex + 1) % this.tips.length;
      tipText.style.opacity = '0';
      tipText.style.transform = 'translateY(4px)';
      tipText.style.transition = 'all 0.25s ease';
      
      setTimeout(() => {
        tipText.textContent = `"${this.tips[this.currentIndex]}"`;
        tipText.style.opacity = '1';
        tipText.style.transform = 'translateY(0)';
      }, 250);
    }, 12000);
  }
};

// ==========================================================================
// Web Audio API Synthesizer (Zero External Dependencies)
// ==========================================================================
const SoundFX = {
  ctx: null,

  getContext() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.ctx = new AudioContext();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
    return this.ctx;
  },

  playBeep(freq = 440, duration = 0.12, type = 'sine') {
    const ctx = this.getContext();
    if (!ctx) return;
    try {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch(e) {}
  },

  playSosAlert() {
    const ctx = this.getContext();
    if (!ctx) return;
    try {
      [880, 660, 920, 1100].forEach((freq, idx) => {
        setTimeout(() => {
          this.playBeep(freq, 0.22, 'sawtooth');
        }, idx * 170);
      });
    } catch(e) {}
  },

  playSafeChime() {
    const ctx = this.getContext();
    if (!ctx) return;
    try {
      [523.25, 659.25, 783.99].forEach((freq, idx) => {
        setTimeout(() => {
          this.playBeep(freq, 0.3, 'triangle');
        }, idx * 140);
      });
    } catch(e) {}
  }
};

// ==========================================================================
// Accessibility Engine
// ==========================================================================
const Accessibility = {
  state: {
    lightMode: localStorage.getItem('resq_light_mode') === 'true',
    highContrast: localStorage.getItem('resq_high_contrast') === 'true',
    largeText: localStorage.getItem('resq_large_text') === 'true',
    reduceMotion: localStorage.getItem('resq_reduce_motion') === 'true',
    voiceAssist: localStorage.getItem('resq_voice_assist') === 'true',
  },

  init() {
    this.applyAll();
    this.bindEvents();
  },

  applyAll() {
    document.body.classList.toggle('light-mode', this.state.lightMode);
    document.body.classList.toggle('high-contrast', this.state.highContrast);
    document.body.classList.toggle('large-text', this.state.largeText);
    document.body.classList.toggle('reduce-motion', this.state.reduceMotion);

    const lightToggle = document.getElementById('toggle-light-mode');
    if (lightToggle) lightToggle.checked = this.state.lightMode;

    const contrastToggle = document.getElementById('toggle-high-contrast');
    if (contrastToggle) contrastToggle.checked = this.state.highContrast;

    const textToggle = document.getElementById('toggle-large-text');
    if (textToggle) textToggle.checked = this.state.largeText;

    const motionToggle = document.getElementById('toggle-reduce-motion');
    if (motionToggle) motionToggle.checked = this.state.reduceMotion;

    const voiceToggle = document.getElementById('toggle-voice-assist');
    if (voiceToggle) voiceToggle.checked = this.state.voiceAssist;
  },

  toggle(key) {
    this.state[key] = !this.state[key];
    localStorage.setItem(`resq_${key.replace(/([A-Z])/g, '_$1').toLowerCase()}`, this.state[key]);
    this.applyAll();
    this.saveToServer();
    
    if (this.state[key]) {
      SoundFX.playBeep(440, 0.08);
    }
  },

  saveToServer() {
    fetch('/api/accessibility/update/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
      },
      body: JSON.stringify({
        dark_mode: !this.state.lightMode,
        high_contrast: this.state.highContrast,
        large_text: this.state.largeText,
        reduce_motion: this.state.reduceMotion,
        voice_assist: this.state.voiceAssist,
      })
    }).catch(() => {});
  },

  speak(text) {
    if (!this.state.voiceAssist && !window.forceSpeech) return;
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  },

  bindEvents() {
    const quickThemeBtn = document.getElementById('quick-theme-toggle');
    if (quickThemeBtn) {
      quickThemeBtn.addEventListener('click', () => {
        this.toggle('lightMode');
        showToast(this.state.lightMode ? 'Daylight Shift Activated' : 'Tactical Dark Mode Activated', 'info');
      });
    }

    const quickA11yBtn = document.getElementById('quick-a11y-toggle');
    if (quickA11yBtn) {
      quickA11yBtn.addEventListener('click', () => {
        const modal = document.getElementById('a11y-modal');
        if (modal) modal.classList.add('active');
      });
    }

    document.querySelectorAll('[data-speak]').forEach(elem => {
      elem.addEventListener('focus', () => {
        this.speak(elem.getAttribute('data-speak'));
      });
    });
  }
};

// ==========================================================================
// Toast Notification Engine
// ==========================================================================
function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'emergency' || type === 'error') icon = '🚨';
  if (type === 'warning') icon = '⚠️';

  toast.innerHTML = `
    <span style="font-size: 1.3rem;">${icon}</span>
    <div style="flex: 1; font-weight: 800; font-size: 0.92rem;">${message}</div>
    <button style="background: none; border: none; font-size: 1.1rem; color: var(--text-muted); cursor: pointer;" onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(toast);

  if (type === 'emergency') {
    SoundFX.playSosAlert();
  } else if (type === 'success') {
    SoundFX.playSafeChime();
  } else {
    SoundFX.playBeep(520, 0.08);
  }

  Accessibility.speak(message);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-15px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('active');
}

document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('active');
  }
});

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  Accessibility.init();
  SafetyTips.init();
});
