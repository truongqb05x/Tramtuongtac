


/* ============ USERS DATA RENDERING ============ */
function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function initUsers(ALL_USERS) {
  const ITEMS_PER_PAGE = 10;
  let currentPage = 1;

  function renderTable() {
    const searchEl = document.getElementById('searchUsers');
    const statEl = document.getElementById('filterStatus');

    if(!searchEl || !statEl) return;

    const q = (searchEl.value || '').toLowerCase();
    const stat = statEl.value;

    let list = ALL_USERS.slice();
    if(q) {
      list = list.filter(x => x.name.toLowerCase().includes(q) || x.email.toLowerCase().includes(q));
    }
    if(stat) list = list.filter(x => x.status === stat);

    const tbody = document.getElementById('usersTableBody');
    const pgContainer = document.getElementById('paginationContainer');
    
    if(!tbody || !pgContainer) return;

    if(!list.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:2.5rem;color:var(--muted);font-size:.8125rem">Không tìm thấy người dùng nào.</td></tr>';
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

    tbody.innerHTML = pageData.map(u => {
      let initials = u.name !== 'N/A' ? u.name.charAt(0).toUpperCase() : 'U';
      let statusCls = u.status === 'active' ? 'ok' : 'danger';
      return `
        <tr>
          <td>
            <div class="user-cell">
              <span class="mini-avatar">${initials}</span>
              <div>
                <div class="user-cell-name">${escapeHtml(u.name)}</div>
                <div class="user-cell-handle">${escapeHtml(u.email)}</div>
              </div>
            </div>
          </td>
          <td><span class="cell-strong">${u.role}</span></td>
          <td><span class="cell-mono">${escapeHtml(u.balance)}</span></td>
          <td><span class="cell-strong">${u.activeJobs}</span></td>
          <td><span class="cell-mono">${escapeHtml(u.joinDate)}</span></td>
          <td><span class="status-pill ${statusCls}">${escapeHtml(u.statusLabel)}</span></td>
          <td class="cell-right">
            <button class="btn btn-secondary btn-sm" onclick="showToast('Đang mở hồ sơ ${u.email}')">Chi tiết</button>
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

  const searchUsers = document.getElementById('searchUsers');
  const filterStatus = document.getElementById('filterStatus');

  if(searchUsers) searchUsers.addEventListener('input', () => { currentPage = 1; renderTable(); });
  if(filterStatus) filterStatus.addEventListener('change', () => { currentPage = 1; renderTable(); });

  renderTable();
}
