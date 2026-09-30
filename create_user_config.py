import os
import glob

def update_app_py():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    if '/admin/user-config' not in content:
        route = "\n@app.route('/admin/user-config')\ndef admin_user_config():\n    return render_template('admin/user_config.html')\n"
        content = content.replace("def admin_reports():\n    return render_template('admin/reports.html')\n", 
                                  "def admin_reports():\n    return render_template('admin/reports.html')\n" + route)
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)

def update_html_files():
    files = glob.glob('templates/admin/*.html')
    
    old_js = """
      if (view === 'tasks') {
        window.location.href = '/admin/tasks';
        return;
      } else if (view === 'transactions') {
        window.location.href = '/admin/transactions';
        return;
      } else if (view === 'users') {
        window.location.href = '/admin/users';
        return;
      } else if (view === 'reports') {
        window.location.href = '/admin/reports';
        return;
      } else if (view === 'dashboard') {
        window.location.href = '/admin';
        return;
      }
"""
    new_js = """
      if (view === 'tasks') {
        window.location.href = '/admin/tasks';
        return;
      } else if (view === 'transactions') {
        window.location.href = '/admin/transactions';
        return;
      } else if (view === 'users') {
        window.location.href = '/admin/users';
        return;
      } else if (view === 'reports') {
        window.location.href = '/admin/reports';
        return;
      } else if (view === 'user-config') {
        window.location.href = '/admin/user-config';
        return;
      } else if (view === 'dashboard') {
        window.location.href = '/admin';
        return;
      }
"""
    
    for path in files:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace js routing if not already replaced
            if "view === 'user-config'" not in content:
                content = content.replace(old_js, new_js)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)

def create_user_config_html():
    with open('templates/admin/layout_admin.html', 'r', encoding='utf-8') as f:
        layout = f.read()

    # Update title
    layout = layout.replace('<title>Quản trị — TRAODOI</title>', '<title>Duyệt tài khoản liên kết - Admin Console</title>')
    layout = layout.replace('<h1 class="page-title-admin" id="pageTitle">Dashboard</h1>', '<h1 class="page-title-admin" id="pageTitle">Cấu hình tài khoản</h1>')

    # Update active menu
    layout = layout.replace('<button class="sidebar-link active" data-view="dashboard">', '<button class="sidebar-link" data-view="dashboard">')
    layout = layout.replace('<button class="sidebar-link" data-view="user-config">', '<button class="sidebar-link active" data-view="user-config">')

    content = """
      <div class="panel">
        <div class="filter-bar-admin">
          <div class="filter-search-admin">
            <svg width="12" height="12" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <circle cx="6" cy="6" r="4.5" stroke="currentColor" stroke-width="1.3"/>
              <path d="M9.5 9.5L12.5 12.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
            <input type="text" placeholder="Tìm theo tên user, link tài khoản liên kết..." id="searchAccounts" />
          </div>
          <select class="filter-select-admin" id="filterPlatform">
            <option value="">Tất cả nền tảng</option>
            <option value="Facebook">Facebook</option>
            <option value="TikTok">TikTok</option>
            <option value="Instagram">Instagram</option>
            <option value="Youtube">Youtube</option>
          </select>
          <select class="filter-select-admin" id="filterSystemCheck">
            <option value="">Tất cả cảnh báo</option>
            <option value="clone">Nghi ngờ Clone</option>
            <option value="ok">Bình thường</option>
          </select>
          <select class="filter-select-admin" id="filterStatus">
            <option value="">Tất cả trạng thái</option>
            <option value="pending">Chờ duyệt</option>
            <option value="approved">Đã duyệt</option>
            <option value="rejected">Bị từ chối / Khóa</option>
          </select>
        </div>

        <table class="data-table-admin" style="min-width: 900px;">
          <thead>
            <tr>
              <th>User (Chủ sở hữu)</th>
              <th>Nền tảng</th>
              <th>Tài khoản liên kết / Link</th>
              <th>Đánh giá hệ thống</th>
              <th>Trạng thái</th>
              <th class="right">Hành động</th>
            </tr>
          </thead>
          <tbody id="accountsTableBody">
            <!-- JS -->
          </tbody>
        </table>
      </div>
"""
    layout = layout.replace('<!-- Nội dung trang con sẽ nằm ở đây -->', content)

    js_content = """<script>
(function(){
  'use strict';
  
  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  const ALL_ACCOUNTS = [
    { id: 'A-101', owner: 'Trần Văn A', handle: '@tranvana', platform: 'Facebook', linkedName: 'Tran Van A Real', link: 'https://fb.com/profile.php?id=10008...', sysCheck: 'Nghi ngờ Clone (Avatar trống, 0 bạn bè)', sysCode: 'clone', status: 'pending', statusLabel: 'Chờ duyệt' },
    { id: 'A-102', owner: 'Lê Thị B', handle: '@lethib', platform: 'TikTok', linkedName: 'lethiB_dance', link: 'https://tiktok.com/@lethib_dance', sysCheck: 'Bình thường (10k Followers)', sysCode: 'ok', status: 'pending', statusLabel: 'Chờ duyệt' },
    { id: 'A-103', owner: 'Phạm Văn C', handle: '@phamvanc', platform: 'Instagram', linkedName: 'pham.c_99', link: 'https://instagram.com/pham.c_99', sysCheck: 'Bình thường', sysCode: 'ok', status: 'approved', statusLabel: 'Đã duyệt' },
    { id: 'A-104', owner: 'Nguyễn Thị D', handle: '@nguyenthid', platform: 'Youtube', linkedName: 'Nguyen Thi D Vlogs', link: 'https://youtube.com/channel/UC...', sysCheck: 'Bình thường', sysCode: 'ok', status: 'approved', statusLabel: 'Đã duyệt' },
    { id: 'A-105', owner: 'Hoàng Văn E', handle: '@hoangvane', platform: 'Facebook', linkedName: 'User123456', link: 'https://fb.com/user123456', sysCheck: 'Nghi ngờ Clone (Tên không hợp lệ, mới tạo 1 ngày)', sysCode: 'clone', status: 'pending', statusLabel: 'Chờ duyệt' },
    { id: 'A-106', owner: 'Vũ Thị F', handle: '@vuthif', platform: 'TikTok', linkedName: 'bot_spam_001', link: 'https://tiktok.com/@bot_spam_001', sysCheck: 'Clone (Trùng IP với 5 tài khoản khác)', sysCode: 'clone', status: 'rejected', statusLabel: 'Bị khóa' }
  ];

  function renderTable() {
    const q = (document.getElementById('searchAccounts').value || '').toLowerCase();
    const plat = document.getElementById('filterPlatform').value;
    const sys = document.getElementById('filterSystemCheck').value;
    const stat = document.getElementById('filterStatus').value;

    let list = ALL_ACCOUNTS.slice();
    if(q) {
      list = list.filter(x => x.owner.toLowerCase().includes(q) || x.handle.toLowerCase().includes(q) || x.linkedName.toLowerCase().includes(q));
    }
    if(plat) list = list.filter(x => x.platform === plat);
    if(sys) list = list.filter(x => x.sysCode === sys);
    if(stat) list = list.filter(x => x.status === stat);

    const tbody = document.getElementById('accountsTableBody');
    if(!list.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2.5rem;color:var(--muted);font-size:.8125rem">Không tìm thấy tài khoản nào.</td></tr>';
      return;
    }

    tbody.innerHTML = list.map(a => {
      let stClass = 'mute';
      if(a.status === 'pending') stClass = 'warn';
      if(a.status === 'approved') stClass = 'ok';
      if(a.status === 'rejected') stClass = 'danger';

      let sysClass = a.sysCode === 'clone' ? 'color:var(--danger);font-weight:500' : 'color:var(--success);';

      let actions = '';
      if(a.status === 'pending') {
        actions = `
          <button class="btn btn-success btn-sm" onclick="showToast('Đã duyệt tài khoản ${a.linkedName}')">Duyệt</button>
          <button class="btn btn-danger btn-sm" onclick="showToast('Từ chối/Khóa tài khoản ${a.linkedName}')">Từ chối / Khóa</button>
        `;
      } else if (a.status === 'approved') {
        actions = `
          <button class="btn btn-danger btn-sm" onclick="showToast('Đã khóa tài khoản ${a.linkedName}')">Khóa tài khoản này</button>
        `;
      } else {
        actions = `<span class="cell-mono" style="color:var(--muted)">Đã khóa</span>`;
      }

      let linkDisplay = `<a href="${a.link}" target="_blank" style="color:var(--accent);text-decoration:underline;">${escapeHtml(a.linkedName)}</a>`;

      return `
        <tr>
          <td>
            <div class="user-cell">
              <span class="mini-avatar">${escapeHtml(a.owner.charAt(0))}</span>
              <div>
                <div class="user-cell-name">${escapeHtml(a.owner)}</div>
                <div class="user-cell-handle">${escapeHtml(a.handle)}</div>
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
  }

  document.getElementById('searchAccounts').addEventListener('input', renderTable);
  document.getElementById('filterPlatform').addEventListener('change', renderTable);
  document.getElementById('filterSystemCheck').addEventListener('change', renderTable);
  document.getElementById('filterStatus').addEventListener('change', renderTable);

  renderTable();
})();
</script>
"""
    layout = layout.replace('<!-- Script riêng của trang con sẽ nằm ở đây -->', js_content)

    with open('templates/admin/user_config.html', 'w', encoding='utf-8') as f:
        f.write(layout)

update_app_py()
update_html_files()
create_user_config_html()
print("User Config page created and linked!")
