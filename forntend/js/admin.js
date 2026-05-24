const API = "http://127.0.0.1:5000";

let allItems        = [];
let activeMealFilter= 'all';

// ══════════════════════════════════════════════
// LOAD ALL MENU ITEMS
// ══════════════════════════════════════════════
async function loadAll() {
  const container = document.getElementById('menuList');
  container.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--muted);font-size:0.85rem">⟳ Loading…</div>`;

  try {
    const meals   = ['breakfast','lunch','snacks','dinner'];
    const results = await Promise.all(meals.map(m => fetch(`${API}/menu?type=${m}`).then(r=>r.json())));
    allItems = [];
    results.forEach((arr, mi) => arr.forEach(item => allItems.push({...item, _meal: meals[mi]})));
    renderList();
  } catch {
    container.innerHTML = `<div class="empty"><span class="empty-icon">⚠️</span><p>Cannot reach server</p></div>`;
    showToast('⚠️ Server offline', 'error');
  }
}

// ══════════════════════════════════════════════
// RENDER LIST
// ══════════════════════════════════════════════
function renderList() {
  const container = document.getElementById('menuList');
  const filtered  = activeMealFilter === 'all'
    ? allItems
    : allItems.filter(i => i._meal === activeMealFilter);

  container.innerHTML = '';
  if (!filtered.length) {
    container.innerHTML = `<div class="empty"><span class="empty-icon">📭</span><p>No items</p></div>`;
    return;
  }

  filtered.forEach((item, i) => {
    const el = document.createElement('div');
    el.className = 'admin-item';
    el.style.animationDelay = `${i*0.04}s`;

    // Stars display
    const stars = item.avg_rating || 0;
    const starsHtml = [1,2,3,4,5].map(n =>
      `<span style="color:${n<=Math.round(stars)?'var(--gold)':'#333'};font-size:0.85rem">★</span>`
    ).join('');

    // Thumbnail
    const thumb = item.photo_url
      ? `<img src="${API}${item.photo_url}" class="admin-thumb" alt="">`
      : `<div class="admin-thumb-placeholder">${mealEmoji(item._meal)}</div>`;

    el.innerHTML = `
      <div class="admin-thumb-wrap">${thumb}</div>
      <div class="admin-item-info">
        <strong>${escHtml(item.item_name)}
          <span class="meal-badge">${capitalize(item._meal)}</span>
        </strong>
        <span>📅 ${capitalize(item.day)} &nbsp;·&nbsp; ⏱ ${item.start_time||'—'} – ${item.end_time||'—'}</span>
        <span class="admin-stars">${starsHtml} <em>${stars>0?stars.toFixed(1)+' ('+item.rating_count+')':"No ratings"}</em></span>
      </div>
      <div class="admin-item-actions">
        <label class="photo-upload-btn" title="Upload photo">
          📷
          <input type="file" accept="image/*" style="display:none"
                 onchange="uploadPhoto(${item.id}, this)">
        </label>
        <button class="delete-btn" onclick="deleteMenu(${item.id}, this)">🗑</button>
      </div>`;
    container.appendChild(el);
  });
}

// ══════════════════════════════════════════════
// FILTER BY MEAL
// ══════════════════════════════════════════════
function filterMeal(meal, btn) {
  activeMealFilter = meal;
  document.querySelectorAll('.meal-pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  renderList();
}

// ══════════════════════════════════════════════
// ADD MENU  (supports photo via FormData)
// ══════════════════════════════════════════════
async function addMenu() {
  const day      = document.getElementById('day').value.trim().toLowerCase();
  const meal     = document.getElementById('meal').value.trim().toLowerCase();
  const item     = document.getElementById('item').value.trim();
  const start    = document.getElementById('start').value.trim();
  const end      = document.getElementById('end').value.trim();
  const photoEl  = document.getElementById('photoFile');
  const photoFile= photoEl && photoEl.files[0] ? photoEl.files[0] : null;

  if (!day || !meal || !item) {
    showToast('❗ Fill Day, Meal & Food Item', 'error');
    ['day','meal','item'].forEach(id => { if(!document.getElementById(id).value.trim()) shakeEl(document.getElementById(id)); });
    return;
  }

  const btn = document.querySelector('.add-btn');
  btn.disabled = true;
  btn.innerHTML = '<span>⟳</span> Adding…';

  try {
    let res;
    if (photoFile) {
      // multipart/form-data
      const fd = new FormData();
      fd.append('day',       day);
      fd.append('meal_type', meal);
      fd.append('item_name', item);
      fd.append('start_time',start || '07:00 AM');
      fd.append('end_time',  end   || '09:00 AM');
      fd.append('photo',     photoFile);
      res = await fetch(`${API}/add-menu`, { method:'POST', body: fd });
    } else {
      res = await fetch(`${API}/add-menu`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ day, meal_type:meal, item_name:item,
          start_time: start||'07:00 AM', end_time: end||'09:00 AM' }),
      });
    }

    if (!res.ok) throw new Error();
    ['day','meal','item','start','end'].forEach(id => document.getElementById(id).value = '');
    if (photoEl) photoEl.value = '';
    document.getElementById('photoPreview').style.display = 'none';

    showToast(`✅ "${item}" added!`, 'success');
    await loadAll();

  } catch {
    showToast('❌ Failed to add. Check server.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>✦</span> Add to Menu';
  }
}

// ══════════════════════════════════════════════
// UPLOAD PHOTO (for existing item)
// ══════════════════════════════════════════════
async function uploadPhoto(menuId, inputEl) {
  const file = inputEl.files[0];
  if (!file) return;

  const fd = new FormData();
  fd.append('photo', file);

  showToast('📷 Uploading photo…', 'info');

  try {
    const res = await fetch(`${API}/menu/${menuId}/photo`, { method:'POST', body: fd });
    if (!res.ok) throw new Error();
    showToast('📷 Photo updated!', 'success');
    await loadAll();
  } catch {
    showToast('❌ Photo upload failed.', 'error');
  }
}

// ══════════════════════════════════════════════
// PREVIEW PHOTO BEFORE ADDING
// ══════════════════════════════════════════════
function previewPhoto(input) {
  const preview = document.getElementById('photoPreview');
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = e => {
      preview.src   = e.target.result;
      preview.style.display = 'block';
    };
    reader.readAsDataURL(input.files[0]);
  }
}

// ══════════════════════════════════════════════
// DELETE MENU ITEM
// ══════════════════════════════════════════════
async function deleteMenu(id, btnEl) {
  if (!confirm('Remove this item from the menu?')) return;
  btnEl.disabled  = true;
  btnEl.textContent = '…';

  try {
    await fetch(`${API}/delete-menu/${id}`, { method:'DELETE' });
    const row = btnEl.closest('.admin-item');
    row.style.transition = 'opacity .3s,transform .3s';
    row.style.opacity = '0'; row.style.transform = 'translateX(30px)';
    setTimeout(() => { allItems = allItems.filter(i=>i.id!==id); renderList(); showToast('🗑 Removed','info'); }, 300);
  } catch {
    showToast('❌ Delete failed.','error');
    btnEl.disabled = false; btnEl.innerHTML = '🗑';
  }
}

// ══════════════════════════════════════════════
// LOAD & DISPLAY ALERTS
// ══════════════════════════════════════════════
async function loadAlerts() {
  try {
    const res    = await fetch(`${API}/alerts?hours=24`);
    const alerts = await res.json();
    const panel  = document.getElementById('alertPanel');
    if (!alerts.length) {
      panel.innerHTML = '<div style="color:var(--muted);font-size:0.82rem;padding:0.5rem 0">✅ No alerts in last 24h</div>';
      return;
    }
    panel.innerHTML = alerts.map(a => `
      <div class="alert-item ${a.resolved ? 'resolved' : a.type.includes('critical')||a.type==='negative_spike' ? 'critical' : 'warning'}">
        <div class="alert-item-icon">${a.type === 'negative_spike' ? '🚨' : '⭐'}</div>
        <div class="alert-item-body">
          <div class="alert-item-msg">${escHtml(a.message)}</div>
          <div class="alert-item-time">${a.triggered_at}${a.resolved?' · ✅ Resolved':''}</div>
        </div>
        ${!a.resolved ? `<button class="resolve-btn" onclick="resolveAlert(${a.id},this)">Resolve</button>` : ''}
      </div>`).join('');
  } catch {
    document.getElementById('alertPanel').innerHTML =
      '<div style="color:var(--muted);font-size:0.82rem">Could not load alerts</div>';
  }
}

async function resolveAlert(id, btn) {
  btn.disabled = true; btn.textContent = '…';
  try {
    await fetch(`${API}/alerts/${id}/resolve`, { method:'POST' });
    showToast('✅ Alert resolved','success');
    await loadAlerts();
  } catch {
    showToast('❌ Failed','error'); btn.disabled=false; btn.textContent='Resolve';
  }
}

// ══════════════════════════════════════════════
// UTILS
// ══════════════════════════════════════════════
function showToast(msg, type='info') {
  document.querySelector('.toast')?.remove();
  const t = document.createElement('div');
  t.className=`toast ${type}`; t.textContent=msg;
  document.body.appendChild(t);
  setTimeout(()=>{ t.classList.add('hide'); setTimeout(()=>t.remove(),350); },3500);
}
function capitalize(s){ return s?s.charAt(0).toUpperCase()+s.slice(1):''; }
function escHtml(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function shakeEl(el){
  el.style.borderColor='rgba(255,107,202,0.6)';
  el.style.boxShadow='0 0 0 3px rgba(255,107,202,0.12)';
  setTimeout(()=>{ el.style.borderColor=''; el.style.boxShadow=''; },1200);
}
function mealEmoji(meal){
  return {breakfast:'🌅',lunch:'☀️',snacks:'🍿',dinner:'🌙'}[meal]||'🍽️';
}

// ══════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════
window.addEventListener('DOMContentLoaded', () => {
  loadAll();
  loadAlerts();
  // Poll alerts every 60s
  setInterval(loadAlerts, 60000);
});