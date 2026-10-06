


/* ============ USER CONFIG DATA RENDERING ============ */
function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function initUserConfig(ALL_ACCOUNTS) {
  const ITEMS_PER_PAGE = 10;
  let currentPage = 1;

  function renderTable() {
    const searchEl = document.getElementById('searchAccounts');
    const platEl = document.getElementById('filterPlatform');
    const sysEl = document.getElementById('filterSystemCheck');
    const statEl = document.getElementById('filterStatus');

    if(!searchEl || !platEl || !sysEl || !statEl) return;

    const q = (searchEl.value || '').toLowerCase();
    const plat = platEl.value;
    const sys = sysEl.value;
    const stat = statEl.value;

    let list = ALL_ACCOUNTS.slice();
    if(q) {
      list = list.filter(x => x.owner.toLowerCase().includes(q) || x.email.toLowerCase().includes(q) || x.linkedName.toLowerCase().includes(q));
    }
    if(plat) list = list.filter(x => x.platform === plat);
    if(sys) list = list.filter(x => x.sysCode === sys);
    if(stat) list = list.filter(x => x.status === stat);

    const tbody = document.getElementById('accountsTableBody');
    const pgContainer = document.getElementById('paginationContainer');
    
    if(!tbody || !pgContainer) return;

    if(!list.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2.5rem;color:var(--muted);font-size:.8125rem">Không tìm thấy tài khoản nào.</td></tr>';
      pgContainer.innerHTML = '';
      return;
    }

    const totalItems = list.length;
    const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
    
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIdx = startIdx + ITEMS_PER_PAGE;
    const pageData = list.slice(startIdx, endIdx);

    tbody.innerHTML = pageData.map(a => {
      let stClass = 'mute';
      if(a.status === 'pending') stClass = 'warn';
      if(a.status === 'active') stClass = 'ok';
      if(a.status === 'blocked') stClass = 'danger';

      let sysClass = a.sysCode === 'clone' ? 'color:var(--danger);font-weight:500' : 'color:var(--success);';

      let actions = '';
      if(a.status === 'pending') {
        actions = `
          <button class="btn btn-success btn-sm" onclick="approveAccount(${a.raw_id})">Duyệt</button>
          <button class="btn btn-danger btn-sm" onclick="blockAccount(${a.raw_id})">Từ chối / Vô hiệu hóa</button>
        `;
      } else if (a.status === 'active') {
        actions = `
          <button class="btn btn-danger btn-sm" onclick="blockAccount(${a.raw_id})">Vô hiệu hóa tài khoản này</button>
        `;
      } else {
        actions = `
          <button class="btn btn-success btn-sm" onclick="approveAccount(${a.raw_id})">Khôi phục</button>
        `;
      }

      let linkDisplay = `<a href="${a.link}" target="_blank" style="color:var(--accent);text-decoration:underline;">${escapeHtml(a.linkedName)}</a>`;

      return `
        <tr>
          <td>
            <div class="user-cell">
              <span class="mini-avatar">${escapeHtml(a.owner !== 'N/A' ? a.owner.charAt(0).toUpperCase() : 'U')}</span>
              <div>
                <div class="user-cell-name">${escapeHtml(a.owner)}</div>
                <div class="user-cell-handle">${escapeHtml(a.email)}</div>
              </div>
            </div>
          </td>
          <td><span style="font-weight:500">${escapeHtml(a.platform)}</span></td>
          <td>
            <div style="font-size:13px;max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${linkDisplay}</div>
          </td>
          <td>
            <div style="font-size:12.5px;max-width:260px;line-height:1.4;${sysClass}">${escapeHtml(a.sysCheck)}</div>
          </td>
          <td><span class="status-pill ${stClass}">${a.statusLabel}</span></td>
          <td class="cell-right">
            <div class="row-actions">${actions}</div>
          </td>
        </tr>
      `;
    }).join('');

    const startShow = startIdx + 1;
    const endShow = Math.min(endIdx, totalItems);
    
    let html = `
      <div class="pagination">
        <div class="pagination-info">Hiển thị ${startShow} - ${endShow} trên tổng số ${totalItems}</div>
        <div class="pager">
          <button ${currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1})">«</button>
    `;
    
    let maxPagesToShow = 5;
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
    
    if (endPage - startPage < maxPagesToShow - 1) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }
    
    if (startPage > 1) {
        html += `<button onclick="goToPage(1)">1</button>`;
        if (startPage > 2) html += `<button disabled>...</button>`;
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<button disabled>...</button>`;
        html += `<button onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }

    html += `
          <button ${currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1})">»</button>
        </div>
      </div>
    `;
    pgContainer.innerHTML = html;
  }

  window.goToPage = function(p) {
    currentPage = p;
    renderTable();
  };

  const searchAccounts = document.getElementById('searchAccounts');
  const filterPlatform = document.getElementById('filterPlatform');
  const filterSystemCheck = document.getElementById('filterSystemCheck');
  const filterStatus = document.getElementById('filterStatus');

  if(searchAccounts) searchAccounts.addEventListener('input', () => { currentPage = 1; renderTable(); });
  if(filterPlatform) filterPlatform.addEventListener('change', () => { currentPage = 1; renderTable(); });
  if(filterSystemCheck) filterSystemCheck.addEventListener('change', () => { currentPage = 1; renderTable(); });
  if(filterStatus) filterStatus.addEventListener('change', () => { currentPage = 1; renderTable(); });

  renderTable();

  window.approveAccount = function(id) {
    if(!confirm("Bạn có chắc muốn duyệt/khôi phục tài khoản này?")) return;
    fetch(`/admin/api/social-accounts/${id}/approve`, { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        if(data.success) {
          showToast("Thành công!");
          setTimeout(() => location.reload(), 1000);
        } else {
          alert("Lỗi: " + data.message);
        }
      }).catch(() => alert("Lỗi kết nối!"));
  };

  window.blockAccount = function(id) {
    if(!confirm("Bạn có chắc muốn vô hiệu hóa tài khoản này?")) return;
    fetch(`/admin/api/social-accounts/${id}/block`, { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        if(data.success) {
          showToast("Đã vô hiệu hóa thành công!");
          setTimeout(() => location.reload(), 1000);
        } else {
          alert("Lỗi: " + data.message);
        }
      }).catch(() => alert("Lỗi kết nối!"));
  };
}
