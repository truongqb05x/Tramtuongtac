/* ============ TOAST ============ */
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

window.showLoading = function(show) {
    const loader = document.getElementById('globalLoading');
    if (loader) {
      if (show) loader.classList.add('active');
      else loader.classList.remove('active');
    }
};

document.addEventListener("DOMContentLoaded", () => {
    /* ============ HEADER USER MENU ============ */
    const userAvatarBtn = document.getElementById('userAvatarBtn');
    const userDropdownMenu = document.getElementById('userDropdownMenu');
    if (userAvatarBtn && userDropdownMenu) {
        userAvatarBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdownMenu.classList.toggle('show');
        });
        document.addEventListener('click', (e) => {
            if (!userDropdownMenu.contains(e.target)) {
                userDropdownMenu.classList.remove('show');
            }
        });
    }

    /* ============ HEADER MOBILE MENU ============ */
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    if (hamburgerBtn && mobileMenu) {
        hamburgerBtn.addEventListener('click', () => {
            const open = mobileMenu.classList.toggle('open');
            hamburgerBtn.classList.toggle('open', open);
            hamburgerBtn.setAttribute('aria-expanded', open);
        });
    }
});

const SecurityConfig = {
    DEVTOOLS_THRESHOLD: 300, // Ngưỡng phát hiện DevTools
    CHECK_INTERVAL: 1000,
    WARNING_DURATION: 3000,
    REDIRECT_DELAY: 5000
};

class SecurityManager {
    constructor() {
        this.devToolsOpened = false;
        this.warningElement = null;
        this.lastInnerHeight = window.innerHeight;
        this.isFormFocused = false;
        this.isKeyboardVisible = false;
    }

    init() {
        try {
            this.addWarningStyles();
            this.createWarningElement();
            this.startDevToolsDetection();
        } catch (error) {
            console.error('Security initialization error:', error);
        }
    }

    addWarningStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .security-warning {
                color: #d32f2f;
                background-color: #ffebee;
                padding: 15px;
                border-radius: 5px;
                margin: 20px auto;
                max-width: 800px;
                text-align: center;
                display: none;
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 9999;
            }
        `;
        document.head.appendChild(style);
    }

    createWarningElement() {
        this.warningElement = document.createElement('div');
        this.warningElement.id = 'warning-message';
        this.warningElement.className = 'security-warning';
        document.body.appendChild(this.warningElement);
    }

    showWarning(message) {
        if (this.warningElement) {
            this.warningElement.textContent = message;
            this.warningElement.style.display = 'block';
            setTimeout(() => {
                this.warningElement.style.display = 'none';
            }, SecurityConfig.WARNING_DURATION);
        }
    }

    startDevToolsDetection() {
        const isMobile = /Mobi|Android/i.test(navigator.userAgent);

        const checkDevTools = () => {
            try {
                const currentInnerHeight = window.innerHeight;
                if (Math.abs(currentInnerHeight - this.lastInnerHeight) > 100) {
                    this.isKeyboardVisible = currentInnerHeight < this.lastInnerHeight;
                }
                this.lastInnerHeight = currentInnerHeight;

                if (this.isFormFocused || this.isKeyboardVisible) {
                    return;
                }

                const widthDiff = window.outerWidth - window.innerWidth;
                const heightDiff = window.outerHeight - window.innerHeight;
                let isDebugging = false;

                if (!isMobile) {
                    const start = Date.now();
                    debugger;
                    if (Date.now() - start > 100) {
                        isDebugging = true;
                    }
                }

                const threshold = isMobile ? 500 : SecurityConfig.DEVTOOLS_THRESHOLD;

                if ((widthDiff > threshold || heightDiff > threshold || isDebugging) && !this.devToolsOpened) {
                    this.devToolsOpened = true;
                    document.body.innerHTML = `
                        <div class="security-warning" style="display: block;">
                            <h1>Cảnh báo bảo mật</h1>
                            <p>DevTools đã được phát hiện. Vui lòng đóng DevTools để tiếp tục sử dụng trang web.</p>
                            <p>Trang sẽ tự động tải lại sau ${SecurityConfig.REDIRECT_DELAY / 1000} giây...</p>
                        </div>`;
                    setTimeout(() => {
                        window.location.reload();
                    }, SecurityConfig.REDIRECT_DELAY);
                }
            } catch (error) {
                console.error('DevTools check error:', error);
            }
        };

        setInterval(checkDevTools, SecurityConfig.CHECK_INTERVAL);
        window.addEventListener('load', checkDevTools);
        window.addEventListener('resize', checkDevTools);
    }
}

// SecurityManager is now available globally.
window.SecurityManager = SecurityManager;
window.SecurityConfig = SecurityConfig;

// Auto-initialize DevTools blocking
const securityManager = new window.SecurityManager();
securityManager.init();

/* ============ GIAO DIỆN VÀ ĐIỀU HƯỚNG ADMIN ============ */
document.addEventListener("DOMContentLoaded", () => {

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
});
