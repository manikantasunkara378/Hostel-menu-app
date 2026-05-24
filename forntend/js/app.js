const API = "http://127.0.0.1:5000";

const MEAL_EMOJIS = {
  breakfast: ['🥞','🍳','🥐','🥣','🫓','🧇','🍵','🫖'],
  lunch    : ['🍛','🍲','🥗','🍜','🫕','🍚','🌮','🥘'],
  snacks   : ['🍿','🧆','🥨','🍩','🧁','🍪','🥜','🍫'],
  dinner   : ['🍽️','🍖','🥩','🫔','🍝','🥣','🍜','🫛'],
};

let currentType = 'breakfast';

// ══════════════════════════════════════════════
// LOAD MENU
// ══════════════════════════════════════════════
async function loadMenu(type, clickedTab) {
  currentType = type;

  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  if (clickedTab) clickedTab.classList.add('active');

  const container = document.getElementById('menu');
  container.innerHTML = Array(6).fill('<div class="shimmer-card"></div>').join('');

  try {
    const res  = await fetch(`${API}/menu?type=${type}`);
    const data = await res.json();
    await delay(280);

    container.innerHTML = '';
    if (!data.length) {
      container.innerHTML = `<div class="empty"><span class="empty-icon">🍽️</span><p>No ${type} items today</p></div>`;
      return;
    }

    const emojis = MEAL_EMOJIS[type] || ['🍴'];
    data.forEach((item, i) => {
      const emoji = emojis[i % emojis.length];
      const card  = document.createElement('div');
      card.className = 'card';
      card.style.animationDelay = `${i * 0.07}s`;

      // ── Photo or emoji ──
      const photoHtml = item.photo_url
        ? `<div class="card-photo-wrap">
             <img src="${API}${item.photo_url}" alt="${escHtml(item.item_name)}" class="card-photo"
                  onerror="this.parentElement.innerHTML='<span class=card-emoji>${emoji}</span>'">
           </div>`
        : `<span class="card-emoji">${emoji}</span>`;

      // ── Star rating display ──
      const stars     = item.avg_rating || 0;
      const starsHtml = buildStarsDisplay(stars, item.rating_count);

      card.innerHTML = `
        ${photoHtml}
        <h3>${escHtml(item.item_name)}</h3>
        <div class="day-tag">📅 ${capitalize(item.day)}</div>
        ${item.start_time ? `<div class="time-chip">⏱ ${item.start_time}${item.end_time ? ' – '+item.end_time : ''}</div>` : ''}
        <div class="badge available">✓ Available</div>
        <div class="rating-row" id="rating-${item.id}">
          ${starsHtml}
        </div>
        <div class="star-input" id="stars-${item.id}">
          ${buildStarInput(item.id)}
        </div>`;

      container.appendChild(card);
    });

  } catch {
    container.innerHTML = `<div class="empty"><span class="empty-icon">⚠️</span><p>Could not connect to server</p></div>`;
    showToast('⚠️ Server unreachable', 'error');
  }
}

// ── Star display (read-only) ──────────────────
function buildStarsDisplay(avg, count) {
  const full    = Math.round(avg);
  const stars   = [1,2,3,4,5].map(n =>
    `<span class="star ${n <= full ? 'filled' : ''}">★</span>`
  ).join('');
  const label   = count ? `${avg.toFixed(1)} (${count})` : 'No ratings yet';
  return `<div class="stars-display">${stars}</div><div class="rating-label">${label}</div>`;
}

// ── Star input (clickable) ────────────────────
function buildStarInput(menuId) {
  return `<div class="stars-pick" data-id="${menuId}">
    ${[1,2,3,4,5].map(n =>
      `<span class="star-pick" data-v="${n}" onclick="submitRating(${menuId},${n},this)">★</span>`
    ).join('')}
  </div>
  <div class="rate-label">Rate this dish</div>`;
}

// ══════════════════════════════════════════════
// SUBMIT STAR RATING
// ══════════════════════════════════════════════
async function submitRating(menuId, stars, el) {
  // Highlight picked stars
  const picker = el.closest('.stars-pick');
  picker.querySelectorAll('.star-pick').forEach(s => {
    s.classList.toggle('picked', parseInt(s.dataset.v) <= stars);
  });
  picker.style.pointerEvents = 'none';

  try {
    const res  = await fetch(`${API}/rate`, {
      method : 'POST',
      headers: {'Content-Type':'application/json'},
      body   : JSON.stringify({ menu_id: menuId, stars }),
    });
    const data = await res.json();

    // Update display
    const ratingRow = document.getElementById(`rating-${menuId}`);
    if (ratingRow) ratingRow.innerHTML = buildStarsDisplay(data.avg_rating, data.rating_count);

    showToast(`⭐ Rated ${stars} star${stars>1?'s':''}! Avg: ${data.avg_rating}★`, 'success');

    // ── Handle alerts from server ──
    if (data.alerts && data.alerts.length) {
      data.alerts.forEach(a => showAlertBanner(a));
    }

  } catch {
    showToast('❌ Rating failed. Try again.', 'error');
    picker.style.pointerEvents = '';
  }
}

// ══════════════════════════════════════════════
// SEND COMPLAINT
// ══════════════════════════════════════════════
async function sendComplaint() {
  const text = document.getElementById('text').value.trim();
  if (!text) { showToast('✏️ Write something first', 'error'); return; }

  try {
    const res  = await fetch(`${API}/complaint`, {
      method : 'POST',
      headers: {'Content-Type':'application/json'},
      body   : JSON.stringify({ message: text, meal_type: currentType }),
    });
    const data = await res.json();
    document.getElementById('text').value = '';

    // Show tags returned by server
    const tagStr = data.tags && data.tags.length ? ' · Tags: ' + data.tags.join(', ') : '';
    const sentimentIcon = data.sentiment === 'positive' ? '😊' : data.sentiment === 'negative' ? '😤' : '😐';
    showToast(`${sentimentIcon} Feedback sent! ${tagStr}`, 'success');

    if (data.alerts && data.alerts.length) {
      data.alerts.forEach(a => showAlertBanner(a));
    }

  } catch {
    showToast('❌ Failed to send. Try again.', 'error');
  }
}

// ══════════════════════════════════════════════
// ALERT BANNER  (push alert popup)
// ══════════════════════════════════════════════
function showAlertBanner(alert) {
  const existing = document.getElementById('alert-banner');
  if (existing) existing.remove();

  const banner = document.createElement('div');
  banner.id    = 'alert-banner';
  banner.className = `alert-banner ${alert.level || 'warning'}`;
  banner.innerHTML = `
    <div class="alert-icon">${alert.level === 'critical' ? '🚨' : '⚠️'}</div>
    <div class="alert-msg">${escHtml(alert.message)}</div>
    <button class="alert-close" onclick="this.parentElement.remove()">✕</button>`;
  document.body.appendChild(banner);

  // Auto-dismiss after 8s
  setTimeout(() => banner && banner.remove(), 8000);
}

// ══════════════════════════════════════════════
// TOAST
// ══════════════════════════════════════════════
function showToast(msg, type = 'info') {
  document.querySelector('.toast')?.remove();
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => { t.classList.add('hide'); setTimeout(() => t.remove(), 350); }, 3500);
}

// ══════════════════════════════════════════════
// UTILS
// ══════════════════════════════════════════════
const delay      = ms => new Promise(r => setTimeout(r, ms));
const capitalize = s  => s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
const escHtml    = s  => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

// ══════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════
window.addEventListener('DOMContentLoaded', () => {
  const firstTab = document.querySelector('.tab');
  if (firstTab) loadMenu('breakfast', firstTab);
});