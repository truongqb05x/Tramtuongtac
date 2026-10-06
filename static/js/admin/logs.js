


/* ============ LOGS DATA RENDERING ============ */
function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function initLogs(ALL_LOGS) {
  function renderTable() {
    const searchEl = document.getElementById('searchLogs');
    const typeEl = document.getElementById('filterType');
    
    if (!searchEl || !typeEl) return;
    
    const q = (searchEl.value || '').toLowerCase();
    const typeVal = typeEl.value;

    let list = ALL_LOGS.slice();
    if(q) {
      list = list.filter(x => 
        x.action.toLowerCase().includes(q) || 
        x.actor.toLowerCase().includes(q) || 
        x.details.toLowerCase().includes(q) || 
        x.id.toLowerCase().includes(q)
      );
    }
    if(typeVal) list = list.filter(x => x.type === typeVal);

    const tbody = document.getElementById('logsTableBody');
    if(!tbody) return;

    if(!list.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2.5rem;color:var(--muted);font-size:.8125rem">Không tìm thấy nhật ký phù hợp.</td></tr>';
      return;
    }

    tbody.innerHTML = list.map(a => {
      let stClass = 'mute';
      if(a.type === 'admin') stClass = 'info';
      if(a.type === 'system') stClass = 'mute';
      if(a.type === 'user') stClass = 'warn';

      return `
        <tr>
          <td>
            <div class="cell-mono" style="color:var(--ink-soft)">${escapeHtml(a.time)}</div>
            <div class="cell-mono" style="font-size:10px; margin-top:2px;">#${a.id}</div>
          </td>
          <td><span style="font-weight:500">${escapeHtml(a.actor)}</span></td>
          <td><span class="status-pill ${stClass}">${a.typeLabel}</span></td>
          <td><div style="font-weight:500; color:var(--ink);">${escapeHtml(a.action)}</div></td>
          <td>
            <div style="font-size:12.5px;max-width:300px;line-height:1.4; color:var(--muted);">${escapeHtml(a.details)}</div>
            <div class="cell-mono" style="font-size:11px; margin-top:4px;">IP: ${escapeHtml(a.ip)}</div>
          </td>
          <td class="cell-right">
            <button class="btn btn-ghost btn-sm" onclick="showToast('Xem chi tiết Log ${a.id}')">Chi tiết</button>
          </td>
        </tr>
      `;
    }).join('');
  }

  const searchLogs = document.getElementById('searchLogs');
  const filterType = document.getElementById('filterType');
  
  if (searchLogs) {
    searchLogs.addEventListener('input', renderTable);
    searchLogs.addEventListener('keypress', function(e){
      if(e.key === 'Enter') e.preventDefault();
    });
  }
  
  if (filterType) {
    filterType.addEventListener('change', renderTable);
  }

  renderTable();
}
