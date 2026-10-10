function initHeader() {
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
}

if (document.readyState === 'loading') {
    document.addEventListener("DOMContentLoaded", initHeader);
} else {
    initHeader();
}