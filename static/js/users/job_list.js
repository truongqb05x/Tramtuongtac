(function () {
  'use strict';

  /* ============ DATA ============ */
  const TASKS = window.TASKS || [];
  const DAILY_LIMIT = window.DAILY_LIMIT || 200;

  const ACCEPTED = new Set();
  const IN_PROGRESS = new Set();
  let selectedTask = null;
  let acceptedToday = 0; // In a real system, this would come from the server

  /* ============ RENDER TABLE ============ */
  const taskBody = document.getElementById('taskBody');

  function renderTasks(list) {
    taskBody.innerHTML = '';
    if (!list.length) {
      taskBody.innerHTML = '<tr><td colspan="3"><div class="empty-state">Không có nhiệm vụ phù hợp với bộ lọc hiện tại.</div></td></tr>';
      return;
    }
    list.forEach(t => {
      const tr = document.createElement('tr');
      tr.dataset.id = t.id;
      if (selectedTask && selectedTask.id === t.id) tr.classList.add('selected');
      const isAccepted = ACCEPTED.has(t.id);

      let btnText = 'Đi làm';
      if (isAccepted) btnText = 'Đã nhận';
      else if (IN_PROGRESS.has(t.id)) btnText = 'Nhận credit';

      tr.innerHTML = `
        <td data-label="Nhiệm vụ">
          <div class="platform-cell">
            <span class="platform-mark">${(PLATFORM[t.platform.toLowerCase()] || {}).icon || t.mark}</span>
            <div>
              <div class="platform-name">${t.platform}</div>
              <div class="platform-sub">${t.title}</div>
            </div>
          </div>
        </td>
        <td data-label="Loại"><span style="color:var(--ink-soft)">${t.category}</span></td>
        <td data-label="">
          <button class="row-btn ${isAccepted ? 'done' : ''}" data-row-btn>
            ${btnText}
          </button>
        </td>
      `;
      const btn = tr.querySelector('[data-row-btn]');
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (isAccepted) return;
        if (IN_PROGRESS.has(t.id)) {
          btn.disabled = true;
          btn.innerText = 'Đang kiểm tra...';
          showLoading(true);
          fetch(`/api/jobs/${t.id}/verify`, { method: 'POST' })
            .then(res => res.json())
            .then(json => {
              showLoading(false);
              if (json.success) {
                ACCEPTED.add(t.id);
                acceptedToday++;
                showToast('Đã nhận thành công ' + json.reward + ' Credit!');
                renderTasks(getFiltered());
              } else {
                IN_PROGRESS.delete(t.id);
                btn.disabled = false;
                btn.innerText = 'Đi làm';

                let errorMsg = json.message || 'Lỗi kiểm tra nhiệm vụ.';
                // Nếu thông báo lỗi chứa thông tin từ Facebook API thì hiển thị lỗi hệ thống
                if (errorMsg.toLowerCase().includes('facebook') ||
                  errorMsg.toLowerCase().includes('api') ||
                  errorMsg.toLowerCase().includes('graph') ||
                  errorMsg.toLowerCase().includes('error')) {
                  errorMsg = 'Chưa hoàn thành nhiệm vụ';
                }
                showToast(errorMsg);
              }
            })
            .catch(err => {
              showLoading(false);
              IN_PROGRESS.delete(t.id);
              btn.disabled = false;
              btn.innerText = 'Đi làm';
              showToast('Lỗi kết nối. Vui lòng thử lại!');
            });
        } else {
          if (acceptedToday >= DAILY_LIMIT) {
            showToast(`Bạn đã đạt giới hạn ${DAILY_LIMIT} nhiệm vụ/ngày. Quay lại vào ngày mai!`);
            return;
          }
          if (t.url) {
            window.open(t.url, '_blank');
          } else {
            showToast('Không tìm thấy đường link nhiệm vụ.');
          }
          IN_PROGRESS.add(t.id);
          renderTasks(getFiltered());
        }
      });
      taskBody.appendChild(tr);
    });
  }

  function closeModal(id) {
    document.getElementById(id).classList.remove('active');
    if (!document.querySelector('.modal-overlay.active')) {
      document.body.style.overflow = '';
    }
  }
  window.closeModal = closeModal;

  document.querySelectorAll('[data-close]').forEach(b => {
    b.addEventListener('click', () => {
      const overlay = b.closest('.modal-overlay');
      if (overlay) closeModal(overlay.id);
    });
  });
  document.querySelectorAll('.modal-overlay').forEach(o => {
    o.addEventListener('click', e => { if (e.target === o) closeModal(o.id); });
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(m => closeModal(m.id));
    }
  });

  /* ============ FILTERS ============ */
  const filters = { platform: new Set(), category: new Set() };

  function renderFilterUI() {
    const platformCounts = {};
    const categoryCounts = {};

    TASKS.forEach(t => {
      const p = (t.platform || '').toLowerCase();
      let c = (t.category || '').toLowerCase();

      if (['like', 'tym', 'haha', 'thương thương', 'wow', 'sad', 'buồn', 'phẫn nộ', 'cảm xúc'].some(k => c.includes(k))) {
        c = 'tương tác';
      }

      if (p) platformCounts[p] = (platformCounts[p] || 0) + 1;
      if (c) categoryCounts[c] = (categoryCounts[c] || 0) + 1;
    });

    const pfContainer = document.getElementById('platformFilters');
    const cfContainer = document.getElementById('categoryFilters');

    if (pfContainer) pfContainer.innerHTML = '';
    if (cfContainer) cfContainer.innerHTML = '';

    function createLabel(group, val, labelText, count) {
      const label = document.createElement('label');
      label.className = 'filter-item';
      const isChecked = filters[group].has(val) ? 'checked' : '';
      label.innerHTML = `<input type="checkbox" data-filter="${group}" value="${val}" ${isChecked} /> ${labelText} <span class="filter-count">${count}</span>`;
      return label;
    }

    const platformKeys = Object.keys(platformCounts);
    const categoryKeys = Object.keys(categoryCounts);

    // Auto-select if there is only 1 option
    if (platformKeys.length === 1 && filters.platform.size === 0) {
      filters.platform.add(platformKeys[0]);
    }
    if (categoryKeys.length === 1 && filters.category.size === 0) {
      filters.category.add(categoryKeys[0]);
    }

    const platformMap = { 'facebook': 'Facebook', 'instagram': 'Instagram', 'tiktok': 'TikTok', 'youtube': 'YouTube', 'website': 'Website' };

    for (const [p, count] of Object.entries(platformCounts)) {
      if (pfContainer) pfContainer.appendChild(createLabel('platform', p, platformMap[p] || (p.charAt(0).toUpperCase() + p.slice(1)), count));
    }

    const catMap = { 'theo dõi': 'Theo dõi', 'tương tác': 'Tương tác', 'bình luận': 'Bình luận', 'xem': 'Xem & Truy cập', 'chia sẻ': 'Chia sẻ' };
    for (const [c, count] of Object.entries(categoryCounts)) {
      if (cfContainer) cfContainer.appendChild(createLabel('category', c, catMap[c] || (c.charAt(0).toUpperCase() + c.slice(1)), count));
    }

    // Attach events
    document.querySelectorAll('[data-filter]').forEach(input => {
      input.addEventListener('change', () => {
        const group = input.dataset.filter;
        const val = input.value;
        if (input.checked) filters[group].add(val);
        else filters[group].delete(val);
        applyFilters();
      });
    });
  }

  renderFilterUI();

  document.getElementById('resetFilters').addEventListener('click', () => {
    filters.platform = new Set();
    filters.category = new Set();
    document.querySelectorAll('[data-filter]').forEach(i => i.checked = false);
    applyFilters();
  });

  const desktopToggleFilter = document.getElementById('desktopToggleFilter');
  if (desktopToggleFilter) {
    desktopToggleFilter.addEventListener('click', () => {
      document.querySelector('.workspace').classList.toggle('collapsed');
    });
    // Align button with the separator
    setTimeout(() => {
      const group1 = document.getElementById('firstFilterGroup');
      if (group1) {
        desktopToggleFilter.style.top = (group1.offsetTop + group1.offsetHeight - 14) + 'px';
      }
    }, 100);
  }

  const platformKey = { 'Facebook': 'facebook', 'Instagram': 'instagram', 'TikTok': 'tiktok', 'YouTube': 'youtube', 'Website': 'website' };
  const PLATFORM = {
    facebook: { icon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z"/></svg>' },
    instagram: { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>' },
    tiktok: { icon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 2.25-1.15 4.34-2.88 5.75-1.74 1.43-4.14 2.1-6.4 1.83-2.18-.27-4.18-1.42-5.48-3.15-1.29-1.72-1.72-4-1.23-6.07.48-2.07 1.83-3.82 3.66-4.8 1.84-.97 4.04-1.22 6.05-.72l.01 4.25c-.97-.24-2.02-.13-2.91.35-.87.48-1.5 1.3-1.7 2.27-.2 1.02.04 2.1.66 2.9.61.79 1.63 1.25 2.64 1.28 1.05.04 2.13-.3 2.83-1.07.72-.78 1.05-1.89 1.02-3 .05-3.92.01-7.85.03-11.78.02-1.4.03-2.8.04-4.2z"/></svg>' },
    youtube: { icon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>' },
    website: { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>' }
  };

  function getFiltered() {
    let list = TASKS.slice().filter(t => !ACCEPTED.has(t.id));

    if (filters.platform.size) {
      list = list.filter(t => filters.platform.has((t.platform || '').toLowerCase()));
    }

    if (filters.category.size) {
      list = list.filter(t => {
        const cat = (t.category || '').toLowerCase();
        for (const q of filters.category) {
          if (q === 'xem' && (cat.includes('xem') || cat.includes('truy cập') || cat.includes('view'))) return true;
          if (q === 'tương tác' && (cat.includes('tương tác') || cat.includes('đăng ký') || cat.includes('like') || cat.includes('tym') || cat.includes('haha') || cat.includes('thương thương') || cat.includes('wow') || cat.includes('sad') || cat.includes('buồn') || cat.includes('phẫn nộ') || cat.includes('cảm xúc'))) return true;
          if (q === 'theo dõi' && (cat.includes('follow') || cat.includes('theo dõi'))) return true;
          if (q === 'bình luận' && (cat.includes('comment') || cat.includes('bình luận'))) return true;
          if (q === 'chia sẻ' && (cat.includes('share') || cat.includes('chia sẻ'))) return true;
          if (cat.includes(q)) return true;
        }
        return false;
      });
    }

    return list;
  }

  let currentPage = 1;
  const ITEMS_PER_PAGE = 10;

  function applyFilters() {
    currentPage = 1;
    updatePageView();
  }

  function updatePageView() {
    const list = getFiltered();
    const total = list.length;
    const totalPages = Math.ceil(total / ITEMS_PER_PAGE) || 1;

    if (currentPage > totalPages) currentPage = totalPages;

    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = Math.min(start + ITEMS_PER_PAGE, total);

    renderTasks(list.slice(start, end));

    document.getElementById('pageInfo').textContent = `Hiển thị ${total === 0 ? 0 : start + 1}–${end} trong ${total} nhiệm vụ`;
    renderPagination(totalPages);
  }

  function renderPagination(totalPages) {
    const pager = document.getElementById('pager');
    if (!pager) return;

    let html = `<button ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}" aria-label="Trang trước">‹</button>`;

    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
        html += `<button class="${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
      } else if (i === currentPage - 2 || i === currentPage + 2) {
        html += `<button disabled>…</button>`;
      }
    }

    html += `<button ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}" aria-label="Trang sau">›</button>`;

    pager.innerHTML = html;

    pager.querySelectorAll('button[data-page]').forEach(btn => {
      btn.addEventListener('click', () => {
        const p = parseInt(btn.dataset.page, 10);
        if (!isNaN(p) && p !== currentPage && p >= 1 && p <= totalPages) {
          currentPage = p;
          updatePageView();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    });
  }

  /* ============ MOBILE FILTER (simple toggle) ============ */
  document.getElementById('mobileFilterBtn').addEventListener('click', () => {
    showToast('Bộ lọc mobile sẽ sớm có — dùng bản desktop để trải nghiệm đầy đủ.');
  });

  /* ============ INIT ============ */
  applyFilters();

})();