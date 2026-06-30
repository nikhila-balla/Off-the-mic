// ── OFF THE MIC — script.js ──────────────────────────────────────

// ── TOAST ──────────────────────────────────────────────────────
function showToast(msg, duration = 2600) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => toast.classList.remove('show'), duration);
}

// ── STREAK & ACTIVITY MANAGEMENT ──────────────────────────────
(function initStreak() {
  const todayDate = new Date();
  const today     = todayDate.toDateString();
  const todayIso  = todayDate.getFullYear() + '-' + String(todayDate.getMonth() + 1).padStart(2, '0') + '-' + String(todayDate.getDate()).padStart(2, '0');
  const lastVisit = localStorage.getItem('otm_last_visit');
  let streak      = parseInt(localStorage.getItem('otm_streak') || '0');

  if (!lastVisit) {
    streak = 1;
  } else if (lastVisit !== today) {
    const diff = (new Date(today) - new Date(lastVisit)) / 86400000;
    streak = diff <= 1 ? streak + 1 : 1;
  }

  localStorage.setItem('otm_streak', streak);
  localStorage.setItem('otm_last_visit', today);

  // Maintain max streak
  let maxStreak = parseInt(localStorage.getItem('otm_max_streak') || '0');
  if (streak > maxStreak) {
    localStorage.setItem('otm_max_streak', streak);
  }

  // Log visitor activity
  let activities = JSON.parse(localStorage.getItem('otm_activity_dates') || '{}');
  if (!activities[todayIso]) {
    activities[todayIso] = 1;
  }
  localStorage.setItem('otm_activity_dates', JSON.stringify(activities));
})();

window.otm_logActivity = function() {
  const todayDate = new Date();
  const todayIso  = todayDate.getFullYear() + '-' + String(todayDate.getMonth() + 1).padStart(2, '0') + '-' + String(todayDate.getDate()).padStart(2, '0');
  let activities  = JSON.parse(localStorage.getItem('otm_activity_dates') || '{}');
  activities[todayIso] = (activities[todayIso] || 0) + 1;
  localStorage.setItem('otm_activity_dates', JSON.stringify(activities));

  // Double check streak triggers
  let streak    = parseInt(localStorage.getItem('otm_streak') || '0');
  let maxStreak = parseInt(localStorage.getItem('otm_max_streak') || '0');
  if (streak > maxStreak) {
    localStorage.setItem('otm_max_streak', streak);
  }
};

// ── PAGE LOAD ANIMATIONS ──────────────────────────────────────
let otmSharedAudioCtx = null;
function getSharedAudioCtx() {
  if (!otmSharedAudioCtx) {
    otmSharedAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (otmSharedAudioCtx.state === 'suspended') {
    otmSharedAudioCtx.resume();
  }
  return otmSharedAudioCtx;
}

window.otm_playPop = function() {
  try {
    const audioCtx = getSharedAudioCtx();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    
    osc.type = 'sine';
    osc.frequency.setValueAtTime(580, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(100, audioCtx.currentTime + 0.08);
    
    gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.08);
    
    osc.start();
    osc.stop(audioCtx.currentTime + 0.09);
  } catch (e) {}
};

document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.card:not([class*="fade-in"])');
  cards.forEach((card, i) => {
    card.style.opacity = 0;
    card.style.transform = 'translateY(20px)';
    setTimeout(() => {
      card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      card.style.opacity = 1;
      card.style.transform = 'translateY(0)';
    }, 100 + i * 100);
  });

  // Bind pop sound to clicks on buttons, triggers, tabs and cards
  setTimeout(() => {
    const clickables = document.querySelectorAll('.btn, .feature-card, .tab-btn, .framework-toggle, .cat-trigger, .diff-trigger, .spin-btn-desktop, .mobile-spin-btn, #logout-btn, #logout-link, #word-of-the-day-banner');
    clickables.forEach(el => {
      el.addEventListener('click', () => {
        if (window.otm_playPop) window.otm_playPop();
      });
    });
  }, 300);
});

// ── BACKEND API HELPERS ───────────────────────────────────────
const isLocal = window.location.protocol === 'file:' || 
                window.location.hostname === 'localhost' || 
                window.location.hostname === '127.0.0.1';
const API_BASE = isLocal ? 'http://127.0.0.1:5000/api' : '/api';

async function apiPost(endpoint, data = {}) {
  try {
    const res = await fetch(API_BASE + endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`API call to ${endpoint} failed:`, err.message);
    return null;
  }
}

async function apiGet(endpoint) {
  try {
    const res = await fetch(API_BASE + endpoint);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`API call to ${endpoint} failed:`, err.message);
    return null;
  }
}

// Convenience wrappers — used by pages when Flask backend is running
window.offTheMic = {
  generateTopic: (category, difficulty) => apiPost('/generate-topic', { category, difficulty }),
  analyseAudio:  (formData) => fetch(API_BASE + '/analyze-speech', { method: 'POST', body: formData }).then(r => r.json()),
  getVocab:      (level) => apiGet(`/get-vocab?level=${level}`),
  getInterviewQ: (type)  => apiGet(`/interview-question?type=${type}`),
  getProgress:   ()      => apiGet('/progress'),
};

// ── SHOW / HIDE PASSWORD ──────────────────────────────────────
function togglePassword(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon  = document.getElementById(iconId);
  if (input.type === 'password') {
    input.type       = 'text';
    icon.textContent = '🙈';
  } else {
    input.type       = 'password';
    icon.textContent = '👁️';
  }
}

// ── PLAYFUL CONFETTI & SOUNDS ──────────────────────────────────
window.otm_triggerConfetti = function() {
  const canvas = document.createElement('canvas');
  canvas.id = 'otm-confetti-canvas';
  canvas.style.position = 'fixed';
  canvas.style.top = '0';
  canvas.style.left = '0';
  canvas.style.width = '100vw';
  canvas.style.height = '100vh';
  canvas.style.pointerEvents = 'none';
  canvas.style.zIndex = '9999';
  document.body.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  let width = canvas.width = window.innerWidth;
  let height = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const colors = ['#e4a959', '#244C7E', '#0A1F3E', '#B89EE8', '#D4C0F9', '#FFD700', '#FF69B4', '#00FFFF'];
  const particles = [];

  for (let i = 0; i < 70; i++) {
    particles.push({
      x: width / 2,
      y: height / 2 + 50,
      radius: Math.random() * 5 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      vx: (Math.random() - 0.5) * 14,
      vy: (Math.random() - 0.7) * 20 - 4,
      gravity: 0.4,
      alpha: 1,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 8
    });
  }

  function animate() {
    ctx.clearRect(0, 0, width, height);
    let alive = false;

    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += p.gravity;
      p.alpha -= 0.015;
      p.rotation += p.rotationSpeed;

      if (p.alpha > 0) {
        alive = true;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rotation * Math.PI / 180);
        ctx.globalAlpha = p.alpha;
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.radius, -p.radius, p.radius * 2, p.radius * 1.5);
        ctx.restore();
      }
    });

    if (alive) {
      requestAnimationFrame(animate);
    } else {
      canvas.remove();
    }
  }

  try {
    const audioCtx = getSharedAudioCtx();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    
    osc.type = 'sine';
    osc.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
    osc.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.1); // E5
    osc.frequency.setValueAtTime(783.99, audioCtx.currentTime + 0.2); // G5
    
    gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
    
    osc.start();
    osc.stop(audioCtx.currentTime + 0.55);
  } catch (e) {
    console.warn('Audio success chime failed:', e);
  }

  animate();
};