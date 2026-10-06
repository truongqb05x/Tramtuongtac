/* ============ NỀN TẢNG VÀ HOẠT ĐỘNG ============ */
function togglePlatform(cb) {
  const body = cb.closest('.cfg-platform-item').querySelector('.cfg-plat-body');
  if (cb.checked) {
    body.style.display = 'block';
  } else {
    body.style.display = 'none';
  }
  showToast(cb.checked ? 'Đã BẬT nền tảng' : 'Đã TẮT nền tảng');
}

function editPrice(btn) {
  const container = btn.closest('.cfg-price-module');
  container.querySelector('.cfg-price-display').style.display = 'none';
  container.querySelector('.cfg-price-input').style.display = 'inline-block';
  container.querySelector('.cfg-price-edit-btn').style.display = 'none';
  container.querySelector('.cfg-price-save-btn').style.display = 'inline-block';
}

function savePrice(btn) {
  const container = btn.closest('.cfg-price-module');
  const newVal = container.querySelector('.cfg-price-input').value;
  container.querySelector('.cfg-price-display').innerText = newVal;
  
  container.querySelector('.cfg-price-display').style.display = 'inline-block';
  container.querySelector('.cfg-price-input').style.display = 'none';
  container.querySelector('.cfg-price-edit-btn').style.display = 'inline-flex';
  container.querySelector('.cfg-price-save-btn').style.display = 'none';
  
  showToast('Cập nhật giá thành công');
  syncToAPI();
}

async function syncToAPI() {
  const platforms = [];
  document.querySelectorAll('.cfg-platform-item').forEach(pNode => {
    const pId = pNode.dataset.id;
    const pName = pNode.querySelector('.plat-name').innerText.trim();
    const pActive = pNode.querySelector('.plat-active-cb').checked;
    
    const activities = [];
    pNode.querySelectorAll('.cfg-act-item').forEach(actNode => {
      const actId = actNode.dataset.id;
      const actName = actNode.querySelector('.act-name').innerText.trim();
      const actPrice = parseFloat(actNode.querySelector('.act-price').value) || 0;
      const actActive = actNode.querySelector('.act-active-cb').checked;
      activities.push({
        id: actId,
        name: actName,
        price: actPrice,
        active: actActive
      });
    });
    
    platforms.push({
      id: pId,
      name: pName,
      active: pActive,
      activities: activities
    });
  });
  
  try {
    const res = await fetch('/admin/api/platforms', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(platforms)
    });
    const json = await res.json();
    if (!json.success) console.error('Failed to sync API');
  } catch(e) {
    console.error(e);
  }
}

let currentPlatformBody = null;

function openAddPlatformModal() {
  document.getElementById('addPlatformModal').style.display = 'flex';
}

function getPlatformIconHTML(name) {
  const n = name.toLowerCase();
  if (n.includes('facebook')) return `<div style="width:36px;height:36px;border-radius:10px;background:#1877f2;color:#fff;display:flex;align-items:center;justify-content:center;"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z"/></svg></div>`;
  if (n.includes('tiktok')) return `<div style="width:36px;height:36px;border-radius:10px;background:#010101;color:#fff;display:flex;align-items:center;justify-content:center;"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.32 6.32 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.22 8.22 0 0 0 4.81 1.53V6.79a4.85 4.85 0 0 1-1.04-.1z"/></svg></div>`;
  if (n.includes('instagram')) return `<div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);color:#fff;display:flex;align-items:center;justify-content:center;"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z"/></svg></div>`;
  if (n.includes('youtube')) return `<div style="width:36px;height:36px;border-radius:10px;background:#ff0000;color:#fff;display:flex;align-items:center;justify-content:center;"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg></div>`;
  if (n.includes('twitter') || n.includes('x.com')) return `<div style="width:36px;height:36px;border-radius:10px;background:#000;color:#fff;display:flex;align-items:center;justify-content:center;"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></div>`;
  return `<div style="width:36px;height:36px;border-radius:10px;background:var(--primary-light);color:var(--primary);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;">${name[0].toUpperCase()}</div>`;
}

function confirmAddPlatform() {
  const name = document.getElementById('newPlatformName').value.trim();
  if(!name) return showToast('Vui lòng nhập tên nền tảng');
  
  const html = `
    <div class="cfg-platform-item">
      <div class="cfg-plat-head">
        <div style="display:flex; align-items:center; gap:12px;">
          ${getPlatformIconHTML(name)}
          <div>
            <div style="font-weight:600; color:var(--ink); font-size:1rem;">${name}</div>
          </div>
        </div>
        <label class="cfg-switch">
          <input type="checkbox" checked onchange="togglePlatform(this)">
          <span class="cfg-slider"></span>
        </label>
      </div>
      <div class="cfg-plat-body">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 1rem;">
          <h4 style="font-size:0.8125rem; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; margin:0;">Các hoạt động con</h4>
          <button class="btn btn-ghost btn-sm" style="padding: 4px 8px; font-size:0.75rem;" onclick="openAddActivityModal(this)">+ Thêm hoạt động</button>
        </div>
        <div class="cfg-act-list">
        </div>
      </div>
    </div>
  `;
  document.getElementById('platformListContainer').insertAdjacentHTML('beforeend', html);
  document.getElementById('addPlatformModal').style.display = 'none';
  document.getElementById('newPlatformName').value = '';
  showToast('Đã thêm nền tảng mới');
  syncToAPI();
}

function openAddActivityModal(btn) {
  currentPlatformBody = btn.closest('.cfg-plat-body').querySelector('.cfg-act-list');
  document.getElementById('addActivityModal').style.display = 'flex';
}

function confirmAddActivity() {
  const name = document.getElementById('newActivityName').value.trim();
  const price = document.getElementById('newActivityPrice').value;
  if(!name) return showToast('Vui lòng nhập tên hoạt động');
  
  const newId = 'act_' + Math.random().toString(36).substr(2, 9);

  const html = `
    <div class="cfg-act-item" data-id="${newId}">
      <div class="act-name" style="font-weight:500; color:var(--ink); font-size:0.875rem; flex:1;">${name}</div>
      <div style="display:flex; align-items:center; gap:16px;">
        <div class="cfg-price-module" style="display:flex; align-items:center; gap:4px;">
          <span style="font-size:0.75rem; color:var(--muted);">Giá/lượt:</span>
          <span class="cfg-price-display" style="font-weight:600; font-size:0.875rem; color:var(--primary);">${price}</span>
          <input type="number" step="any" class="input-field cfg-price-input act-price" value="${price}" style="display:none; width:65px; padding:2px 6px; font-size:0.8125rem; height:26px;" />
          <span style="font-size:0.75rem; font-weight:500; color:var(--ink);">Credits</span>
          
          <button class="btn btn-ghost btn-sm cfg-price-edit-btn" style="padding:4px; display:inline-flex; align-items:center;" onclick="editPrice(this)" title="Sửa giá">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
          </button>
          <button class="btn btn-ghost btn-sm cfg-price-save-btn" style="padding:4px; display:none; align-items:center; color:var(--success);" onclick="savePrice(this)" title="Lưu giá">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
          </button>
        </div>
        <label class="cfg-switch" style="transform: scale(0.85); transform-origin: right;">
          <input type="checkbox" class="act-active-cb" checked onchange="syncToAPI()">
          <span class="cfg-slider"></span>
        </label>
      </div>
    </div>
  `;
  currentPlatformBody.insertAdjacentHTML('beforeend', html);
  document.getElementById('addActivityModal').style.display = 'none';
  document.getElementById('newActivityName').value = '';
  document.getElementById('newActivityPrice').value = '20';
  showToast('Đã thêm hoạt động con');
  syncToAPI();
}


/* ============ HỆ THỐNG VÀ BẢO TRÌ ============ */
async function syncSystemAPI() {
  const maint = document.getElementById('maintToggle').checked;
  const safeMode = document.getElementById('safeModeToggle') ? document.getElementById('safeModeToggle').checked : false;
  try {
    const res = await fetch('/admin/api/system/field', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ key: 'maintenance_mode', value: maint })
    });
    await fetch('/admin/api/system/field', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ key: 'safe_mode', value: safeMode })
    });
  } catch(e) { console.error(e); }
}

async function saveSystemField(key, value, successMsg) {
  if (value === null || value === undefined || (typeof value === 'number' && isNaN(value))) {
    return showToast('Giá trị không hợp lệ');
  }
  try {
    const res = await fetch('/admin/api/system/field', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ key, value })
    });
    const json = await res.json();
    if (json.success) showToast(successMsg || 'Đã lưu');
    else showToast('Lưu thất bại: ' + (json.message || ''));
  } catch(e) {
    showToast('Lỗi kết nối');
    console.error(e);
  }
}

/* ============ TOKEN FACEBOOK API ============ */
function openManageTokenModal() {
  document.getElementById('manageTokenModal').style.display = 'flex';
  document.getElementById('tokenListArea').value = 'Đang tải dữ liệu...';
  document.getElementById('tokenListArea').disabled = true;
  
  fetch('/admin/api/tokens')
    .then(res => res.json())
    .then(json => {
      document.getElementById('tokenListArea').disabled = false;
      if(json.success) {
        document.getElementById('tokenListArea').value = json.tokens.join('\n');
        document.getElementById('tokenCountLabel').innerText = json.tokens.length;
      } else {
        document.getElementById('tokenListArea').value = '';
        showToast('Lỗi tải token: ' + json.message);
      }
    })
    .catch(err => {
      document.getElementById('tokenListArea').disabled = false;
      document.getElementById('tokenListArea').value = '';
      showToast('Lỗi kết nối');
    });
}

function closeManageTokenModal() {
  document.getElementById('manageTokenModal').style.display = 'none';
}

function saveTokens() {
  const lines = document.getElementById('tokenListArea').value.split('\n');
  const tokens = lines.map(t => t.trim()).filter(t => t);
  
  const btn = document.getElementById('btnSaveTokens');
  btn.disabled = true;
  btn.innerText = 'Đang lưu...';
  
  fetch('/admin/api/tokens', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({tokens})
  })
  .then(res => res.json())
  .then(json => {
    btn.disabled = false;
    btn.innerText = 'Lưu Token';
    if(json.success) {
      showToast('Đã lưu thành công ' + tokens.length + ' token!');
      document.getElementById('tokenCountLabel').innerText = tokens.length;
      document.getElementById('tokenCountDisplay').innerText = tokens.length;
      closeManageTokenModal();
    } else {
      showToast('Lỗi lưu token: ' + json.message);
    }
  })
  .catch(err => {
    btn.disabled = false;
    btn.innerText = 'Lưu Token';
    showToast('Lỗi kết nối khi lưu');
  });
}



document.addEventListener("DOMContentLoaded", () => {
  const maintToggle = document.getElementById('maintToggle');
  const maintDot = document.getElementById('maintDot');
  if(maintToggle && maintDot) {
    maintToggle.addEventListener('change', function() {
      if(this.checked) {
        this.nextElementSibling.style.backgroundColor = 'var(--danger)';
        if(maintDot) maintDot.style.left = '23px';
      } else {
        this.nextElementSibling.style.backgroundColor = 'var(--border-strong)';
        if(maintDot) maintDot.style.left = '3px';
      }
    });
  }
});
