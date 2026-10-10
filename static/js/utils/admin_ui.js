/* ============ GIAO DIỆN VÀ ĐIỀU HƯỚNG ADMIN ============ */
function initAdminUI() {
  const sidebar = document.getElementById('sidebar');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const menuToggle = document.getElementById('menuToggle');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.add('on');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('on');
    document.body.style.overflow = '';
  }
  if (menuToggle) menuToggle.addEventListener('click', openSidebar);
  if (sidebarBackdrop) sidebarBackdrop.addEventListener('click', closeSidebar);

  const refreshBtn = document.getElementById('refreshBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', function() {
      this.style.transform = 'rotate(360deg)';
      this.style.transition = 'transform .6s ease';
      setTimeout(() => {
        this.style.transform = '';
        this.style.transition = '';
      }, 600);
      showToast('Đã làm mới dữ liệu.');
    });
  }

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
      if (typeof closeSidebar === 'function') closeSidebar();
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener("DOMContentLoaded", initAdminUI);
} else {
  initAdminUI();
}
