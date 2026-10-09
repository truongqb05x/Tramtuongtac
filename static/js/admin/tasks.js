if (typeof window.showToast !== 'function') {
    window.toastTimer = null;
    window.showToast = function (msg) {
        const toast = document.getElementById('toast');
        const toastMsg = document.getElementById('toastMsg');
        if (!toast || !toastMsg) return;
        toastMsg.textContent = msg;
        toast.classList.add('on');
        clearTimeout(window.toastTimer);
        window.toastTimer = setTimeout(() => toast.classList.remove('on'), 2800);
    };
}

/* ============ TASKS DATA RENDERING ============ */
function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function initTasks(ALL_TASKS) {
  const ITEMS_PER_PAGE = 10;
  let currentPage = 1;

  function renderTable() {
    const searchEl = document.getElementById('searchTasks');
    const platEl = document.getElementById('filterPlatform');
    const statEl = document.getElementById('filterStatus');

    if(!searchEl || !platEl || !statEl) return;

    const q = (searchEl.value || '').toLowerCase();
    const plat = platEl.value;
    const stat = statEl.value;

    let list = ALL_TASKS.slice();
    if(q) {
      list = list.filter(x => x.id.toLowerCase().includes(q) || x.creator.toLowerCase().includes(q) || x.handle.toLowerCase().includes(q));
    }
    if(plat) list = list.filter(x => x.platform === plat);
    if(stat) list = list.filter(x => x.status === stat);

    const tbody = document.getElementById('tasksTableBody');
    const pgContainer = document.getElementById('paginationContainer');
    if(!tbody || !pgContainer) return;
    
    if(!list.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:2.5rem;color:var(--muted);font-size:.8125rem">Không tìm thấy nhiệm vụ nào.</td></tr>';
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

    tbody.innerHTML = pageData.map(t => {
      let stCls = 'mute';
      if(t.status === 'pending') stCls = 'warn';
      if(t.status === 'running') stCls = 'info';
      if(t.status === 'completed') stCls = 'ok';
      if(t.status === 'rejected') stCls = 'danger';

      let actions = '';
      if(t.status === 'pending') {
        actions += `<button class="btn btn-success btn-sm" onclick="showToast('Đã duyệt nhiệm vụ ${t.id}')">Duyệt</button>`;
      } else {
        actions += `<button class="btn btn-secondary btn-sm" onclick="showToast('Đang xem chi tiết ${t.id}')">Chi tiết</button>`;
      }

      if(t.status === 'pending' || t.status === 'running') {
          actions += `<button class="btn btn-primary btn-sm" style="margin-left:5px" onclick="completeJob(${t.raw_id})">Hoàn thành</button>`;
      }

      if(t.status !== 'rejected' && t.status !== 'completed') {
          actions += `<button class="btn btn-danger btn-sm" style="margin-left:5px" onclick="cancelJob(${t.raw_id})">Hủy</button>`;
      } else if (t.status === 'rejected') {
          actions += `<button class="btn btn-success btn-sm" style="margin-left:5px" onclick="restoreJob(${t.raw_id})">Khôi phục</button>`;
      }

      return `
        <tr>
          <td><span class="cell-mono">${t.id}</span></td>
          <td>
            <div class="user-cell">
              <span class="mini-avatar" style="border-radius:6px">${t.creator.charAt(0)}</span>
              <div>
                <div class="user-cell-name">${escapeHtml(t.creator)}</div>
                <div class="user-cell-handle">${escapeHtml(t.handle)}</div>
              </div>
            </div>
          </td>
          <td><span style="font-weight:500">${escapeHtml(t.platform)}</span></td>
          <td>${escapeHtml(t.req)}</td>
          <td>
            <div style="font-weight:600;color:var(--accent)">${t.total_cost} <small style="color:var(--muted);font-weight:400">CR</small></div>
          </td>
          <td><span class="status-pill ${stCls}">${t.statusLabel}</span></td>
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

  const searchTasks = document.getElementById('searchTasks');
  const filterPlatform = document.getElementById('filterPlatform');
  const filterStatus = document.getElementById('filterStatus');

  if(searchTasks) searchTasks.addEventListener('input', () => { currentPage = 1; renderTable(); });
  if(filterPlatform) filterPlatform.addEventListener('change', () => { currentPage = 1; renderTable(); });
  if(filterStatus) filterStatus.addEventListener('change', () => { currentPage = 1; renderTable(); });

  renderTable();

  window.cancelJob = function(jobId) {
      if(!confirm("Bạn có chắc muốn hủy nhiệm vụ này do vi phạm không?")) return;
      fetch(`/admin/api/jobs/${jobId}/cancel`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
      })
      .then(res => res.json())
      .then(data => {
          if(data.success) {
              showToast("Đã hủy nhiệm vụ thành công!");
              setTimeout(() => location.reload(), 1000);
          } else {
              alert("Lỗi: " + data.message);
          }
      })
      .catch(err => alert("Lỗi kết nối!"));
  }
  
  window.restoreJob = function(jobId) {
      if(!confirm("Bạn có chắc muốn khôi phục nhiệm vụ này không?")) return;
      fetch(`/admin/api/jobs/${jobId}/restore`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
      })
      .then(res => res.json())
      .then(data => {
          if(data.success) {
              showToast("Đã khôi phục nhiệm vụ thành công!");
              setTimeout(() => location.reload(), 1000);
          } else {
              alert("Lỗi: " + data.message);
          }
      })
      .catch(err => alert("Lỗi kết nối!"));
  }
  
  window.completeJob = function(jobId) {
      if(!confirm("Bạn có chắc muốn hoàn thành nhiệm vụ này không?")) return;
      fetch(`/admin/api/jobs/${jobId}/complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
      })
      .then(res => res.json())
      .then(data => {
          if(data.success) {
              showToast("Đã hoàn thành nhiệm vụ thành công!");
              setTimeout(() => location.reload(), 1000);
          } else {
              alert("Lỗi: " + data.message);
          }
      })
      .catch(err => alert("Lỗi hệ thống: " + err.message));
  }
}
