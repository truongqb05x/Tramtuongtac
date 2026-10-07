(function(){
  'use strict';

  /* ============ STATE ============ */
  let currentBalance = window.CURRENT_BALANCE || 0;
  let selectedUser = null;
  let currentHistoryTab = 'all';

  let currentSearchResults = [];

  /* ============ HISTORY ============ */
  const HISTORY = window.HISTORY || [];

  /* ============ HELPERS ============ */
  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function formatNumber(n) {
    return Number(n).toLocaleString('vi-VN');
  }

  /* ============ SEARCH & SUGGESTIONS ============ */
  const searchInput = document.getElementById('recipientSearch');
  const searchInputWrap = document.getElementById('searchInputWrap');
  const searchClear = document.getElementById('searchClear');
  const suggestions = document.getElementById('suggestions');
  const selectedUserEl = document.getElementById('selectedUser');
  const recipientHint = document.getElementById('recipientHint');

  let searchTimeout = null;

  function renderSuggestions(query) {
    const q = (query || '').toLowerCase().trim();
    if (!q) {
      suggestions.classList.remove('on');
      return;
    }
    
    // Show loading text if we want, or just wait
    if (searchTimeout) clearTimeout(searchTimeout);
    
    searchTimeout = setTimeout(() => {
      fetch('/api/users/search?q=' + encodeURIComponent(q))
        .then(res => res.json())
        .then(data => {
          if (!data.success) return;
          const matches = data.data;
          currentSearchResults = matches;
          
          if (!matches.length) {
            suggestions.innerHTML = `
              <div class="suggestions-empty">
                <strong>Không tìm thấy người dùng</strong>
                Không có tài khoản nào khớp với "${escapeHtml(query)}". Hãy kiểm tra lại email.
              </div>
            `;
            suggestions.classList.add('on');
            return;
          }

          suggestions.innerHTML = matches.map(u => `
            <div class="suggestion-item" data-user-id="${u.id}">
              <div class="suggestion-info">
                <div class="suggestion-email">${escapeHtml(u.email)}</div>
              </div>
            </div>
          `).join('');

          suggestions.classList.add('on');

          // Bind clicks
          suggestions.querySelectorAll('[data-user-id]').forEach(item => {
            item.addEventListener('click', () => {
              const user = currentSearchResults.find(u => u.id == item.dataset.userId);
              if (user) selectUser(user);
            });
          });
        });
    }, 300);
  }

  function selectUser(user) {
    selectedUser = user;
    searchInput.value = '';
    suggestions.classList.remove('on');
    searchInputWrap.classList.remove('has-value');

    renderSelectedUser();
    validateForm();

    // Hide hint
    recipientHint.style.display = 'none';
  }

  function renderSelectedUser() {
    if (!selectedUser) {
      selectedUserEl.classList.remove('on');
      selectedUserEl.innerHTML = '';
      return;
    }

    selectedUserEl.classList.add('on');
    selectedUserEl.innerHTML = `
      <div class="selected-info">
        <div class="selected-email">${escapeHtml(selectedUser.email)}</div>
      </div>
      <button type="button" class="selected-remove" id="removeSelected" aria-label="Bỏ chọn">×</button>
    `;

    document.getElementById('removeSelected').addEventListener('click', () => {
      selectedUser = null;
      renderSelectedUser();
        validateForm();
      recipientHint.style.display = 'block';
      searchInput.focus();
    });
  }

  searchInput.addEventListener('input', (e) => {
    const val = e.target.value;
    searchInputWrap.classList.toggle('has-value', val.length > 0);
    renderSuggestions(val);
  });

  searchInput.addEventListener('focus', () => {
    if (searchInput.value.trim()) {
      renderSuggestions(searchInput.value);
    }
  });

  searchClear.addEventListener('click', () => {
    searchInput.value = '';
    searchInputWrap.classList.remove('has-value');
    suggestions.classList.remove('on');
    searchInput.focus();
  });

  // Close suggestions on outside click
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-wrap')) {
      suggestions.classList.remove('on');
    }
  });

  /* ============ AMOUNT INPUT ============ */
  const amountInput = document.getElementById('amountInput');
  const amountMinus = document.getElementById('amountMinus');
  const amountPlus = document.getElementById('amountPlus');

  function getAvailableBalance() {
    return currentBalance;
  }

  function getMaxTransfer() {
    return currentBalance;
  }

  amountMinus.addEventListener('click', () => {
    const v = parseInt(amountInput.value, 10) || 50;
    amountInput.value = Math.max(50, v - 10);
    validateForm();
  });

  amountPlus.addEventListener('click', () => {
    const v = parseInt(amountInput.value, 10) || 50;
    const max = getMaxTransfer();
    amountInput.value = Math.min(max, v + 10);
    validateForm();
  });

  amountInput.addEventListener('input', () => {
    let v = parseInt(amountInput.value, 10);
    if (isNaN(v)) v = 0;
    if (v < 0) v = 0;
    validateForm();
  });

  amountInput.addEventListener('change', () => {
    let v = parseInt(amountInput.value, 10) || 50;
    if (v < 50) {
      amountInput.value = 50;
      window.showToast('Số lượng tối thiểu là 50 Credits');
    }
    validateForm();
  });



  /* ============ VALIDATION ============ */
  const submitBtn = document.getElementById('submitBtn');
  const balanceWarning = document.getElementById('balanceWarning');
  const balanceWarningText = document.getElementById('balanceWarningText');

  function validateForm() {
    const amount = parseInt(amountInput.value, 10) || 0;

    // Check balance warning
    let warningOn = false;
    if (amount > currentBalance) {
      warningOn = true;
      balanceWarningText.textContent = `Số dư không đủ. Bạn có ${formatNumber(currentBalance)} Credits nhưng đang cố gửi ${formatNumber(amount)} Credits.`;
    }
    balanceWarning.classList.toggle('on', warningOn);

    // Enable submit only if all valid
    const valid = selectedUser && amount >= 50 && amount <= getMaxTransfer() && !warningOn;
    submitBtn.disabled = !valid;
  }

  /* ============ CONFIRM MODAL ============ */
  const confirmModal = document.getElementById('confirmModal');
  const confirmSubmit = document.getElementById('confirmSubmit');

  submitBtn.addEventListener('click', () => {
    if (!selectedUser) return;
    const amount = parseInt(amountInput.value, 10) || 0;

    document.getElementById('confirmEmail').textContent = selectedUser.email;
    document.getElementById('confirmAmount').textContent = formatNumber(amount) + ' Credits';
    document.getElementById('confirmTotal').textContent = formatNumber(amount) + ' Credits';

    confirmSubmit.disabled = false;

    confirmModal.classList.add('active');
    document.body.style.overflow = 'hidden';
  });

  confirmSubmit.addEventListener('click', () => {
    if (!selectedUser) return;
    const amount = parseInt(amountInput.value, 10) || 0;

    confirmSubmit.disabled = true;
    confirmSubmit.textContent = 'Đang xử lý...';
    
    showLoading(true);

    fetch('/api/transfer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        recipient_id: selectedUser.id,
        amount: amount
      })
    })
    .then(res => res.json())
    .then(data => {
      showLoading(false);
      confirmSubmit.textContent = 'Xác nhận chuyển';
      confirmModal.classList.remove('active');
      document.body.style.overflow = '';
      
      if (data.success) {
        currentBalance = data.new_balance;
        const headerEl = document.getElementById('headerBalance') || document.getElementById('headerCredits');
        if (headerEl) headerEl.textContent = formatNumber(currentBalance);
        
        const availableEl = document.getElementById('availableBalance');
        if (availableEl) availableEl.textContent = formatNumber(currentBalance);
        
        const sidebarEl = document.getElementById('sidebarBalance');
        if (sidebarEl) sidebarEl.innerHTML = formatNumber(currentBalance) + '<small>Credits</small>';
        
        const maxHintEl = document.getElementById('maxTransferHint');
        if (maxHintEl) maxHintEl.textContent = formatNumber(getMaxTransfer());

        // Thêm vào history
        const newTx = {
          id: 'Mới',
          type: 'out',
          user: {
            email: selectedUser.email
          },
          amount: amount,
          time: 'vừa xong',
          ts: Date.now()
        };
        HISTORY.unshift(newTx);

        renderHistory();
        const recipientEmail = selectedUser.email;
        resetForm();

        window.showToast('Đã gửi ' + formatNumber(amount) + ' Credits cho ' + recipientEmail + '.');
      } else {
        alert(data.message || 'Có lỗi xảy ra.');
        confirmSubmit.disabled = false;
      }
    })
    .catch(err => {
      showLoading(false);
      confirmSubmit.textContent = 'Xác nhận chuyển';
      confirmSubmit.disabled = false;
      alert('Lỗi kết nối máy chủ');
    });
  });



  function resetForm() {
    selectedUser = null;
    searchInput.value = '';
    searchInputWrap.classList.remove('has-value');
    amountInput.value = 50;

    renderSelectedUser();
    validateForm();
    recipientHint.style.display = 'block';
  }

  /* ============ MODAL CLOSE ============ */
  document.querySelectorAll('[data-close]').forEach(b => {
    b.addEventListener('click', () => {
      const overlay = b.closest('.modal-overlay');
      if (overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  [confirmModal].forEach(m => {
    m.addEventListener('click', e => {
      if (e.target === m) {
        m.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  /* ============ HISTORY ============ */
  const historyList = document.getElementById('historyList');

  function renderHistory() {
    let list = HISTORY.slice();
    if (currentHistoryTab === 'out') list = list.filter(h => h.type === 'out');
    else if (currentHistoryTab === 'in') list = list.filter(h => h.type === 'in');

    // Update tab counts
    document.querySelector('[data-count="all"]').textContent = HISTORY.length;
    document.querySelector('[data-count="out"]').textContent = HISTORY.filter(h => h.type === 'out').length;
    document.querySelector('[data-count="in"]').textContent = HISTORY.filter(h => h.type === 'in').length;

    if (!list.length) {
      historyList.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="20" height="20" viewBox="0 0 22 22" fill="none" aria-hidden="true">
              <path d="M4 6H18V16H4V6Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
              <path d="M4 10H18" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </div>
          <h3 class="empty-title">Chưa có giao dịch nào</h3>
          <p class="empty-desc">Các giao dịch chuyển và nhận Credits sẽ xuất hiện ở đây.</p>
        </div>
      `;
      return;
    }

    historyList.innerHTML = list.map(h => {
      const isOut = h.type === 'out';
      const sign = isOut ? '−' : '+';
      return `
        <div class="history-row">
          <div class="history-info">
            <div class="history-name">
              ${isOut ? 'Gửi cho' : 'Nhận từ'} ${escapeHtml(h.user.email)}
            </div>
            <div class="history-desc">
              <span>${escapeHtml(h.id)}</span>
            </div>
          </div>
          <div class="history-amount-cell">
            <div class="history-amount ${h.type}">
              ${sign}${formatNumber(h.amount)}<small>Credits</small>
            </div>
            <div class="history-time">${escapeHtml(h.time)}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  document.querySelectorAll('.history-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.history-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentHistoryTab = tab.dataset.tab;
      renderHistory();
    });
  });

  /* ============ ESC ============ */
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(m => {
        m.classList.remove('active');
        document.body.style.overflow = '';
      });
      suggestions.classList.remove('on');
    }
  });


  /* ============ INIT ============ */
  document.getElementById('maxTransferHint').textContent = formatNumber(getMaxTransfer());

  validateForm();
  renderHistory();


})();