


/* ============ DASHBOARD DATA RENDERING ============ */
function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function initDashboard(TASKS, TRANSACTIONS, STATS) {
  /* ============ RENDER TASKS ============ */
  function renderTasks() {
    const tbody = document.querySelectorAll('.data-table-admin tbody')[0];
    if (!tbody) return;
    if (TASKS.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:2.5rem;color:var(--muted);font-size:.8125rem">Chưa có dữ liệu nhiệm vụ.</td></tr>';
      return;
    }
    tbody.innerHTML = TASKS.map(t => {
      const stCls = t.status === 'pending' ? 'warn' : 'info';
      return `
        <tr>
          <td><span class="cell-mono">${t.id}</span></td>
          <td>${escapeHtml(t.creator)}</td>
          <td>${escapeHtml(t.platform)}</td>
          <td>${escapeHtml(t.req)}</td>
          <td><span class="cell-strong">${t.reward}</span></td>
          <td><span class="status-pill ${stCls}">${t.statusLabel}</span></td>
          <td class="cell-right">
            <button class="btn btn-secondary btn-sm" onclick="showToast('Đang mở: ${t.id}')">Xem</button>
          </td>
        </tr>
      `;
    }).join('');
  }

  /* ============ RENDER TRANSACTIONS ============ */
  function renderTransactions() {
    const tbody = document.querySelectorAll('.data-table-admin tbody')[1];
    if (!tbody) return;
    if (TRANSACTIONS.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2.5rem;color:var(--muted);font-size:.8125rem">Chưa có giao dịch nạp tiền.</td></tr>';
      return;
    }
    tbody.innerHTML = TRANSACTIONS.map(tx => {
      return `
        <tr>
          <td><span class="cell-mono">${tx.id}</span></td>
          <td>${escapeHtml(tx.user)}</td>
          <td>${escapeHtml(tx.amount)}</td>
          <td style="color:var(--success);font-weight:600">${escapeHtml(tx.credits)}</td>
          <td>${escapeHtml(tx.time)}</td>
          <td><span class="status-pill ${tx.status}">${tx.statusLabel}</span></td>
        </tr>
      `;
    }).join('');
  }

  /* ============ RENDER STATS ============ */
  function renderStats() {
    const tbody = document.getElementById('statsBody');
    if (!tbody) return;
    if (STATS.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2.5rem;color:var(--muted);font-size:.8125rem">Chưa có dữ liệu.</td></tr>';
      return;
    }
    tbody.innerHTML = STATS.map(s => `
      <tr>
        <td>
          <div class="user-cell">
            <span class="mini-avatar" style="border-radius:4px">${s.platform.charAt(0)}</span>
            <div>
              <div class="user-cell-name">${escapeHtml(s.platform)}</div>
            </div>
          </div>
        </td>
        <td><span class="cell-strong">${escapeHtml(s.active)}</span></td>
        <td><span class="cell-mono">${escapeHtml(s.total)}</span></td>
        <td><span class="cell-strong" style="color:var(--accent)">${escapeHtml(s.reward)}</span></td>
        <td><span class="cell-strong" style="color:var(--success)">${escapeHtml(s.fee)}</span></td>
        <td class="cell-right">
          <span class="status-pill ${s.status}">${escapeHtml(s.statusLabel)}</span>
        </td>
      </tr>
    `).join('');
  }

  renderTasks();
  renderTransactions();
  renderStats();
}

/* ============ REPORT MODAL ============ */
document.addEventListener("DOMContentLoaded", () => {
  const reportModal = document.getElementById('reportModal');
  const applyActionBtn = document.getElementById('applyAction');

  window.openReport = function(id) {
    if (typeof REPORTS !== 'undefined') {
      const r = REPORTS.find(x => x.id === id);
      if (!r) return;
      document.getElementById('reportModalTitle').textContent = 'Chi tiết báo cáo ' + r.id;
      document.getElementById('reportModalSub').textContent =
        'Người bị báo cáo: ' + r.accused + ' (' + r.handle + ') · Báo cáo trước đó: 2 lần';
      document.getElementById('reportReasonText').textContent = r.reason;
    }
    document.getElementById('actionSelect').value = '';
    document.getElementById('actionNote').value = '';
    if (reportModal) reportModal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  if (applyActionBtn) {
    applyActionBtn.addEventListener('click', () => {
      const action = document.getElementById('actionSelect').value;
      const note = document.getElementById('actionNote').value.trim();
      if (!action) { showToast('Vui lòng chọn hành động xử lý.'); return; }
      if (note.length < 10) { showToast('Vui lòng ghi chú lý do (tối thiểu 10 ký tự).'); return; }

      closeModal('reportModal');
      showToast('Đã áp dụng xử lý. Hành động được ghi vào audit log.');
    });
  }

  /* ============ CONFIG MODAL ============ */
  const configModal = document.getElementById('configModal');
  let currentConfig = null;

  document.querySelectorAll('[data-config]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.config;
      const configValues = {
        'fee': { label: 'Phí nền tảng (%)', value: '2.0' },
        'min-deposit': { label: 'Số tiền nạp tối thiểu (VND)', value: '20000' },
        'credit-rate': { label: 'Tỷ lệ quy đổi (VND cho 100 Credits)', value: '1000' },
        'min-reward': { label: 'Thù lao tối thiểu (Credits)', value: '50' },
        'auto-approve': { label: 'Thời gian tự động duyệt (giờ)', value: '24' },
        'max-tasks': { label: 'Giới hạn nhiệm vụ / ngày', value: '100' }
      };
      const cfg = configValues[key];
      if (!cfg) return;
      currentConfig = key;
      document.getElementById('configModalTitle').textContent = 'Chỉnh sửa: ' + cfg.label;
      document.getElementById('configFieldLabel').textContent = cfg.label;
      document.getElementById('configFieldInput').value = cfg.value;
      document.getElementById('configReason').value = '';
      if (configModal) configModal.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
  });

  const saveConfigBtn = document.getElementById('saveConfig');
  if (saveConfigBtn) {
    saveConfigBtn.addEventListener('click', () => {
      const value = document.getElementById('configFieldInput').value.trim();
      const reason = document.getElementById('configReason').value.trim();
      if (!value) { showToast('Vui lòng nhập giá trị mới.'); return; }
      if (reason.length < 10) { showToast('Vui lòng nhập lý do thay đổi (tối thiểu 10 ký tự).'); return; }
      closeModal('configModal');
      showToast('Đã lưu cấu hình. Thay đổi có hiệu lực ngay.');
    });
  }
});
