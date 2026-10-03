
    (function () {
      'use strict';

      /* ============ STATE ============ */
      const PLATFORM_NAMES = {
        facebook: 'Facebook', instagram: 'Instagram', tiktok: 'TikTok',
        youtube: 'YouTube', website: 'Website'
      };
      const PLATFORM_MARKS = {
        facebook: 'FB', instagram: 'IG', tiktok: 'TT',
        youtube: 'YT', website: 'WEB'
      };
      const TYPE_NAMES = {
        follow: 'Theo dõi', like: 'Tương tác',
        comment: 'Bình luận', visit: 'Truy cập',
        fb_like: 'Tăng Like Bài Viết', fb_follow: 'Tăng Follow / Sub', fb_comment: 'Tăng Bình Luận',
        tt_heart: 'Tăng Tim Video', tt_follow: 'Tăng Follow Kênh'
      };
      const FEE_RATE = 0 / 100;

      let balance = 0;

    let createdTasks = 0 || [];

    let nextId = createdTasks.length > 0 ? Math.max(...createdTasks.map(t => t.id)) + 1 : 100;
    let pendingCreate = null;

    /* ============ DOM ============ */
    const platformSelect = document.getElementById('platformSelect');
    const contentUrl = document.getElementById('contentUrl');
    const taskDesc = document.getElementById('taskDesc');
    const slotsInput = document.getElementById('slotsInput');
    const rewardInput = document.getElementById('rewardInput');
    const urlHint = document.getElementById('urlHint');

    const sumSlots = document.getElementById('sumSlots');
    const sumReward = document.getElementById('sumReward');
    const sumSubtotal = document.getElementById('sumSubtotal');
    const sumFee = document.getElementById('sumFee');
    const sumTotal = document.getElementById('sumTotal');
    const balanceWarning = document.getElementById('balanceWarning');
    const balanceMsg = document.getElementById('balanceMsg');
    const submitCreate = document.getElementById('submitCreate');

    const confirmModal = document.getElementById('confirmModal');
    const topupModal = document.getElementById('topupModal');

    /* ============ URL AUTO EXTRACT ID ============ */
    contentUrl.addEventListener('input', function() {
      let val = this.value.trim();
      if (!val.startsWith('http')) return;
      let extractedId = null;
      // Match FB fbid or story_fbid or posts/ videos/
      const fbMatch = val.match(/(?:fbid=|story_fbid=|posts\/|videos\/)(\d+)/);
      if (fbMatch && fbMatch[1]) {
        extractedId = fbMatch[1];
      } else if (val.includes('facebook.com/share/')) {
        // Fetch to backend for resolving redirect URL
        contentUrl.disabled = true;
        const oldVal = contentUrl.value;
        contentUrl.value = 'Đang chuyển đổi link...';
        fetch('/api/convert-url', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({url: val})
        }).then(r => r.json()).then(res => {
          contentUrl.disabled = false;
          if (res.success && res.id) {
            contentUrl.value = res.id;
            showToast('Chuyển đổi thành công');
          } else {
            contentUrl.value = oldVal;
            showToast(res.message || 'Không thể chuyển đổi link, vui lòng tự trích xuất ID.');
            if (res.final_url) console.log('Final URL from backend:', res.final_url);
          }
        }).catch((err) => {
          contentUrl.disabled = false;
          contentUrl.value = oldVal;
          showToast('Lỗi mạng khi chuyển đổi link.');
          console.error(err);
        });
        return;
      } else {
        // TikTok video ID
        const ttMatch = val.match(/\/video\/(\d+)/);
        if (ttMatch && ttMatch[1]) extractedId = ttMatch[1];
        else {
          // Insta or FB short link
          const igMatch = val.match(/\/(?:p|reel)\/([a-zA-Z0-9_-]+)/);
          if (igMatch && igMatch[1]) extractedId = igMatch[1];
        }
      }
      
      if (extractedId) {
        this.value = extractedId;
        showToast('Chuyển đổi thành công');
      }
    });

    /* ============ TYPE CARDS ============ */
    let typeCards = [];
    function attachTypeEvents() {
      typeCards = document.querySelectorAll('.type-card');
      typeCards.forEach(card => {
        const input = card.querySelector('input');
        input.addEventListener('change', () => {
          typeCards.forEach(c => c.classList.toggle('checked', c.querySelector('input').checked));
          const p = parseFloat(card.dataset.price) || 5;
          rewardInput.value = p;
          updateSummary();
        });
      });
    }

    /* ============ FETCH PLATFORMS ============ */
    let platformsData = [];
    fetch('/api/platforms')
      .then(r => r.json())
      .then(res => {
        if(res.success && res.data) {
          platformsData = res.data;
          renderPlatforms(platformsData);
        }
      });

    function renderPlatforms(data) {
      platformSelect.innerHTML = ''; // Bỏ dòng "Chọn nền tảng" mặc định để chọn ngay thằng đầu tiên
      let firstId = null;
      data.forEach(p => {
        if(p.active) {
          if (!firstId) firstId = p.id;
          const opt = document.createElement('option');
          opt.value = p.id;
          opt.textContent = p.name;
          platformSelect.appendChild(opt);
        }
      });
      if (firstId) {
        platformSelect.value = firstId;
        platformSelect.dispatchEvent(new Event('change'));
      }
    }

    function renderActivities(platId) {
      const typeGrid = document.getElementById('typeGrid');
      typeGrid.innerHTML = '';
      const plat = platformsData.find(p => p.id === platId);
      if(!plat || !plat.activities) return;
      
      plat.activities.forEach((act, idx) => {
        if(!act.active) return;
        const lbl = document.createElement('label');
        lbl.className = 'type-card';
        lbl.dataset.type = act.id;
        lbl.dataset.price = act.price;
        
        lbl.innerHTML = `
          <input type="radio" name="taskType" value="${act.id}" ${idx === 0 ? 'checked' : ''} />
          <span class="tc-check"></span>
          <span class="tc-name" style="font-size:0.875rem;">${act.name}</span>
          <span class="tc-desc">${act.price} Credits / lượt</span>
        `;
        typeGrid.appendChild(lbl);
      });
      attachTypeEvents();
      
      // select the first one by default
      const firstInput = typeGrid.querySelector('input[type="radio"]');
      if(firstInput) {
        firstInput.dispatchEvent(new Event('change'));
      }
    }

    /* ============ PLATFORM CHANGE ============ */
    platformSelect.addEventListener('change', () => {
      const v = platformSelect.value;
      if (v) {
        urlHint.textContent = 'Đường dẫn liên quan đến nền tảng ' + v + ' — bao gồm https://';
        renderActivities(v);
      } else {
        urlHint.textContent = 'Dán đường dẫn đầy đủ, bao gồm https://';
        document.getElementById('typeGrid').innerHTML = '';
      }
      updateSummary();
    });

    /* ============ STEPPERS ============ */
    document.querySelectorAll('[data-step]').forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.step === 'slots' ? slotsInput : rewardInput;
        const dir = parseFloat(btn.dataset.dir) || 1;
        const min = parseFloat(target.min) || 0;
        const max = parseFloat(target.max) || 999999;
        let v = parseFloat(target.value) || min;
        v = Math.max(min, Math.min(max, v + dir));
        if (btn.dataset.step !== 'slots') {
          v = Math.round(v * 100) / 100; // handle float precision
        }
        target.value = v;
        updateSummary();
      });
    });

    slotsInput.addEventListener('input', updateSummary);
    slotsInput.addEventListener('change', () => {
      let v = parseInt(slotsInput.value, 10) || 5;
      if (v < 5) {
        slotsInput.value = 5;
        showToast('Số lượng tối thiểu là 5');
      }
      updateSummary();
    });
    rewardInput.addEventListener('input', updateSummary);


    /* ============ FORM INPUT LISTENERS ============ */
    [contentUrl, taskDesc].forEach(el => {
      el.addEventListener('input', updateSummary);
      el.addEventListener('change', updateSummary);
    });

    /* ============ UPDATE SUMMARY ============ */
    function updateSummary() {
      const slots = Math.max(5, parseInt(slotsInput.value, 10) || 0);
      const reward = Math.max(0, parseFloat(rewardInput.value) || 0);
      const subtotal = slots * reward;
      const fee = Math.round(subtotal * FEE_RATE * 100) / 100;
      const total = Math.round((subtotal + fee) * 100) / 100;

      sumSlots.textContent = slots;
      sumReward.textContent = Math.round(reward * 100) / 100 + ' Credits';
      sumSubtotal.textContent = Math.round(subtotal * 100) / 100 + ' Credits';
      sumFee.textContent = Math.round(fee * 100) / 100 + ' Credits';
      sumTotal.textContent = Math.round(total * 100) / 100 + ' Credits';

      // Balance warning — only show when insufficient
      const enough = balance >= total;
      if (enough) {
        balanceWarning.style.display = 'none';
      } else {
        balanceWarning.style.display = 'flex';
        balanceMsg.textContent = 'Số dư không đủ. Cần thêm ' + (Math.round((total - balance) * 100) / 100) + ' Credits.';
      }
      submitCreate.disabled = !enough;
    }

    /* ============ RENDER CREATED TASKS ============ */
    const createdList = document.getElementById('createdList');
    const createdCount = document.getElementById('createdCount');

    function renderCreated() {
      createdCount.textContent = createdTasks.length + ' nhiệm vụ';
      if (!createdTasks.length) {
        createdList.innerHTML =
          '<div class="empty"><div class="empty-title">Chưa có nhiệm vụ nào</div>Tạo nhiệm vụ đầu tiên ở form phía trên.</div>';
        return;
      }

      createdList.innerHTML = '';
      createdTasks.forEach(t => {
        const pct = t.slots > 0 ? Math.round((t.done / t.slots) * 100) : 0;
        let statusCls = 'active';
        let statusText = 'Đang chạy';
        if (t.status === 'done') { statusCls = 'done'; statusText = 'Hoàn thành'; }
        else if (t.status === 'paused') { statusCls = 'paused'; statusText = 'Tạm dừng'; }
        else if (t.status === 'canceled') { statusCls = 'canceled'; statusText = 'Bị hủy'; }

        const row = document.createElement('div');
        row.className = 'created-row';
        row.dataset.id = t.id;
        row.innerHTML = `
        <div class="ct-info">
          <span class="platform-mark">${PLATFORM_MARKS[t.platform] || '??'}</span>
          <div class="ct-text">
            <div class="ct-title">${escapeHtml(t.title)}</div>
            <div class="ct-meta">
              <span>${PLATFORM_NAMES[t.platform] || t.platform}</span>
              <span class="dot">·</span>
              <span>${TYPE_NAMES[t.type] || t.type}</span>
              <span class="dot">·</span>
              <span style="max-width:150px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; display:inline-block; vertical-align:bottom;" title="${t.url}">${t.url || ''}</span>
            </div>
          </div>
        </div>


        <div class="meta-cell" data-label="Tiến độ">
          <div class="progress-mini">
            <div class="pm-bar"><i style="width:${pct}%"></i></div>
            <div class="pm-count">${t.done}<span>/</span>${t.slots}</div>
          </div>
        </div>

        <div class="meta-cell" data-label="Trạng thái">
          <span class="status-badge ${statusCls}">
            <span class="dot"></span>${statusText}
          </span>
        </div>

        <div class="row-actions">
          ${t.status === 'canceled' ? '' : `
          <button class="icon-btn" data-toggle-status>
            ${t.status === 'paused' ? 'Tiếp tục' : t.status === 'done' ? 'Xem' : 'Tạm dừng'}
          </button>
          `}
        </div>
      `;

        // toggle status
        const btn = row.querySelector('[data-toggle-status]');
        if(btn) {
          btn.addEventListener('click', async (e) => {
            e.stopPropagation();
          if (t.status === 'done') {
            showToast('Nhiệm vụ đã hoàn thành, không thể thay đổi.');
            return;
          }
          
          let newStatus = t.status === 'active' ? 'paused' : 'active';
          btn.disabled = true;

          try {
            const response = await fetch(`/jobs/${t.id}/toggle`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ status: newStatus })
            });
            const data = await response.json();
            
            if (data.success) {
              t.status = newStatus;
              showToast(newStatus === 'paused' ? 'Đã tạm dừng nhiệm vụ' : 'Đã tiếp tục nhiệm vụ');
              renderCreated();
            } else {
              showToast(data.message || 'Lỗi khi cập nhật trạng thái');
            }
          } catch (err) {
            console.error(err);
            showToast('Có lỗi xảy ra, vui lòng thử lại.');
          } finally {
            btn.disabled = false;
          }
          });
        }

        createdList.appendChild(row);
      });
    }

    function escapeHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    /* ============ SUBMIT CREATE ============ */
    submitCreate.addEventListener('click', () => {
      if (!validateForm()) return;
      openConfirm();
    });

    function validateForm() {
      if (!platformSelect.value) {
        showToast('Vui lòng chọn nền tảng');
        platformSelect.focus();
        return false;
      }
      const type = document.querySelector('input[name="taskType"]:checked');
      if (!type) {
        showToast('Vui lòng chọn loại nhiệm vụ');
        return false;
      }
      const urlVal = contentUrl.value.trim();
      if (!urlVal) {
        showToast('Vui lòng nhập Link hoặc ID bài viết');
        contentUrl.focus();
        return false;
      }
      
      const isUrl = /^https?:\/\/.+/.test(urlVal);
      const isId = /^[a-zA-Z0-9_-]+$/.test(urlVal);
      
      if (!isUrl && !isId) {
        showToast('Link hoặc ID bài viết không hợp lệ');
        contentUrl.focus();
        return false;
      }
      const slots = parseInt(slotsInput.value, 10) || 0;
      if (slots < 5) {
        showToast('Số lượng tối thiểu phải từ 5 trở lên');
        slotsInput.focus();
        return false;
      }
      return true;
    }

    function openConfirm() {
      const slots = parseInt(slotsInput.value, 10) || 1;
      const reward = parseFloat(rewardInput.value) || 0;
      const subtotal = slots * reward;
      const fee = Math.round(subtotal * FEE_RATE * 100) / 100;
      const total = Math.round((subtotal + fee) * 100) / 100;
      const type = document.querySelector('input[name="taskType"]:checked');

      pendingCreate = {
        platform: platformSelect.value,
        type: type.value,
        desc: taskDesc.value.trim(),
        url: contentUrl.value.trim(),
        slots, reward, total
      };

      document.getElementById('mTitle').textContent =
        PLATFORM_NAMES[pendingCreate.platform] + ' · ' + TYPE_NAMES[pendingCreate.type];
      document.getElementById('mPlatform').textContent = pendingCreate.url;
      document.getElementById('mSlots').textContent = slots;
      document.getElementById('mReward').textContent = reward + ' Credits';
      document.getElementById('mTotal').textContent = total + ' Credits';

      confirmModal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }

    document.getElementById('confirmCreate').addEventListener('click', async () => {
      if (!pendingCreate) return;
      const t = pendingCreate;

      const btn = document.getElementById('confirmCreate');
      const originalText = btn.textContent;
      btn.disabled = true;
      btn.textContent = 'Đang xử lý...';

      try {
        const response = await fetch('/jobs/create', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(t)
        });
        
        const data = await response.json();
        
        if (data.success) {
          balance = data.new_balance;
          document.getElementById('balanceNum').textContent = balance;
          
          let platformKey = (data.job?.platform || t.platform || '').toLowerCase();
          let typeKey = (data.job?.action_type || t.type || '').toLowerCase();

          createdTasks.unshift({
            id: data.job?.id || nextId++,
            platform: platformKey,
            type: typeKey,
            title: (PLATFORM_NAMES[platformKey] || platformKey) + ' · ' + (TYPE_NAMES[typeKey] || typeKey),
            reward: data.job?.price_per_action || t.reward,
            slots: data.job?.quantity || t.slots,
            done: 0,
            status: 'active',
            url: data.job?.target_url || t.url
          });

          closeModal('confirmModal');
          resetForm();
          renderCreated();
          updateSummary();
          showToast('Đã tạo nhiệm vụ thành công!');
        } else {
          alert(data.message || 'Lỗi khi tạo nhiệm vụ');
        }
      } catch (err) {
        console.error(err);
        alert('Có lỗi xảy ra, vui lòng thử lại.');
      } finally {
        btn.disabled = false;
        btn.textContent = originalText;
      }
    });

    /* ============ RESET FORM ============ */
    function resetForm() {
      document.getElementById('createForm').reset();
      typeCards.forEach(c => c.classList.remove('checked'));
      slotsInput.value = 20;
      rewardInput.value = 5;
      urlHint.textContent = 'Dán đường dẫn đầy đủ, bao gồm https://';
      updateSummary();
    }

    /* ============ TOP-UP ============ */
    document.querySelectorAll('[data-modal="topup"]').forEach(b => {
      b.addEventListener('click', () => {
        topupModal.classList.add('active');
        document.body.style.overflow = 'hidden';
      });
    });

    document.querySelectorAll('.topup-opt').forEach(opt => {
      opt.addEventListener('click', () => {
        document.querySelectorAll('.topup-opt').forEach(o => o.classList.remove('checked'));
        opt.classList.add('checked');
        opt.querySelector('input').checked = true;
      });
    });

    document.getElementById('confirmTopup').addEventListener('click', () => {
      const selected = document.querySelector('input[name="topup"]:checked');
      const amount = selected ? parseInt(selected.value, 10) : 100;
      balance += amount;
      document.getElementById('balanceNum').textContent = balance;
      document.getElementById('headerCredits').textContent = balance;
      closeModal('topupModal');
      updateSummary();
      showToast('Đã nạp ' + amount + ' Credits vào tài khoản.');
    });

    /* ============ MODAL HELPERS ============ */
    function closeModal(id) {
      const el = document.getElementById(id);
      if (el) el.classList.remove('active');
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



    

    /* ============ INIT ============ */
    renderCreated();
    updateSummary();

}) ();
  