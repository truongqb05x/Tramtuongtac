


/* ============ REPORTS DATA RENDERING ============ */
function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function initReports(ALL_REPORTS) {
  function renderTable() {
    const searchEl = document.getElementById('searchReports');
    const reasonEl = document.getElementById('filterReason');
    const statEl = document.getElementById('filterStatus');

    if(!searchEl || !reasonEl || !statEl) return;

    const q = (searchEl.value || '').toLowerCase();
    const reason = reasonEl.value;
    const stat = statEl.value;

    let list = ALL_REPORTS.slice();
    if(q) {
      list = list.filter(x => x.id.toLowerCase().includes(q) || x.accused.toLowerCase().includes(q) || x.handle.toLowerCase().includes(q));
    }
    if(reason) list = list.filter(x => x.reasonType === reason);
    if(stat) list = list.filter(x => x.status === stat);

    const tbody = document.getElementById('reportsTableBody');
    if(!tbody) return;

    if(!list.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:2.5rem;color:var(--muted);font-size:.8125rem">Không tìm thấy báo cáo nào.</td></tr>';
      return;
    }

    tbody.innerHTML = list.map(r => {
      let sevClass = 'mute';
      if(r.severity === 'high') sevClass = 'danger';
      if(r.severity === 'medium') sevClass = 'warn';
      if(r.severity === 'low') sevClass = 'info';

      let stClass = 'mute';
      if(r.status === 'pending') stClass = 'warn';
      if(r.status === 'reviewing') stClass = 'info';
      if(r.status === 'resolved') stClass = 'ok';

      let actions = '';
      if(r.status !== 'resolved') {
        actions = `
          <button class="btn btn-danger btn-sm" onclick="showToast('Đã khóa tài khoản ${r.handle}')">Khóa</button>
          <button class="btn btn-secondary btn-sm" onclick="showToast('Bỏ qua báo cáo ${r.id}')">Bỏ qua</button>
        `;
      } else {
        actions = `<span class="cell-mono" style="color:var(--muted)">Đã đóng</span>`;
      }

      let linkDisplay = r.link.startsWith('http') ? `<a href="${r.link}" target="_blank" style="color:var(--accent);text-decoration:underline;">Link dẫn chứng</a>` : `<span class="cell-mono">${r.link}</span>`;

      return `
        <tr>
          <td><span class="cell-mono">${r.id}</span></td>
          <td>
            <div class="user-cell">
              <span class="mini-avatar">${escapeHtml(r.accused.charAt(0))}</span>
              <div>
                <div class="user-cell-name">${escapeHtml(r.accused)}</div>
                <div class="user-cell-handle">${escapeHtml(r.handle)}</div>
              </div>
            </div>
          </td>
          <td><span class="status-pill mute">${escapeHtml(r.reasonType)}</span></td>
          <td>
            <div style="font-size:13px;max-width:250px;white-space:normal;line-height:1.4">${escapeHtml(r.desc)}</div>
            <div style="margin-top:4px;font-size:12px;">${linkDisplay}</div>
          </td>
          <td><span class="status-pill ${sevClass}">${r.severityLabel}</span></td>
          <td><span class="status-pill ${stClass}">${r.statusLabel}</span></td>
          <td class="cell-right">
            <div class="row-actions">${actions}</div>
          </td>
        </tr>
      `;
    }).join('');
  }

  const searchReports = document.getElementById('searchReports');
  const filterReason = document.getElementById('filterReason');
  const filterStatus = document.getElementById('filterStatus');

  if(searchReports) {
    searchReports.addEventListener('input', renderTable);
    searchReports.addEventListener('keypress', function(e){
      if(e.key === 'Enter') e.preventDefault();
    });
  }
  if(filterReason) filterReason.addEventListener('change', renderTable);
  if(filterStatus) filterStatus.addEventListener('change', renderTable);

  renderTable();
}
