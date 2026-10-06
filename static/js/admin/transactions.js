


/* ============ TRANSACTIONS DATA RENDERING ============ */
function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function initTransactions(ALL_TX) {
  const ITEMS_PER_PAGE = 10;
  let currentPage = 1;

  function renderTable() {
    const searchEl = document.getElementById('searchTx');
    const statEl = document.getElementById('filterStatus');

    if(!searchEl || !statEl) return;

    const q = (searchEl.value || '').toLowerCase();
    const stat = statEl.value;

    let list = ALL_TX.slice();
    if(q) {
      list = list.filter(x => x.id.toLowerCase().includes(q) || x.user.toLowerCase().includes(q));
    }
    if(stat) list = list.filter(x => x.status === stat);

    const tbody = document.getElementById('txTableBody');
    const pgContainer = document.getElementById('paginationContainer');
    
    if(!tbody || !pgContainer) return;

    if(!list.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:2.5rem;color:var(--muted);font-size:.8125rem">Không tìm thấy giao dịch nào.</td></tr>';
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

    tbody.innerHTML = pageData.map(tx => {
      let actions = `<button class="btn btn-secondary btn-sm" onclick="showToast('Xem chi tiết ${tx.id}')">Chi tiết</button>`;
      if (tx.status === 'warn') {
        actions = `<button class="btn btn-success btn-sm" onclick="showToast('Duyệt GD ${tx.id}')">Duyệt</button> ` + actions;
      }
      
      let creditStyle = tx.status === 'ok' ? 'color:var(--success);font-weight:600' : 'color:var(--muted);font-weight:500';

      return `
        <tr>
          <td><span class="cell-mono">${tx.id}</span></td>
          <td><span style="font-weight:500;color:var(--ink)">${escapeHtml(tx.user)}</span></td>
          <td><span class="cell-mono">${escapeHtml(tx.method)}</span></td>
          <td><span style="font-weight:500">${escapeHtml(tx.amount)}</span></td>
          <td><span style="${creditStyle}">${escapeHtml(tx.credits)}</span></td>
          <td><span class="cell-mono">${escapeHtml(tx.time)}</span></td>
          <td><span class="status-pill ${tx.status}">${tx.statusLabel}</span></td>
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

  const searchTx = document.getElementById('searchTx');
  const filterStatus = document.getElementById('filterStatus');

  if(searchTx) searchTx.addEventListener('input', () => { currentPage = 1; renderTable(); });
  if(filterStatus) filterStatus.addEventListener('change', () => { currentPage = 1; renderTable(); });

  renderTable();
}
