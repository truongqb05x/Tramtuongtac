(function () {
  'use strict';

  /* ============ TAB SWITCH ============ */
  const panes = { login: document.getElementById('pane-login'), register: document.getElementById('pane-register'), forgot: document.getElementById('pane-forgot') };

  function switchTab(name) {
    if (!panes[name]) name = 'login';
    Object.entries(panes).forEach(([k, el]) => {
      el.classList.toggle('active', k === name);
    });
    document.title = (name === 'login' ? 'Đăng nhập' : (name === 'register' ? 'Đăng ký' : 'Khôi phục mật khẩu')) + ' | TRAMTUONGTAC';
  }

  document.querySelectorAll('[data-switch]').forEach(b => {
    b.addEventListener('click', () => switchTab(b.dataset.switch));
  });

  // Khởi tạo tab mặc định
  switchTab('login');

  /* ============ PASSWORD TOGGLE ============ */
  document.querySelectorAll('[data-toggle]').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.toggle);
      if (!input) return;
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
      btn.innerHTML = show
        ? '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2 2L14 14M6.5 6.7C6.3 6.9 6.2 7.2 6.2 7.5C6.2 8.5 7 9.3 8 9.3C8.3 9.3 8.6 9.2 8.8 9M4.5 4.6C2.9 5.6 1.5 7.3 1 8C1 8 3.5 13 8 13C9.3 13 10.4 12.5 11.4 11.8M13.2 10.3C14.2 9.4 15 8.3 15 8C15 8 12.5 3 8 3C7.5 3 7 3 6.5 3.1" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>'
        : '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M1 8C1 8 3.5 3 8 3C12.5 3 15 8 15 8C15 8 12.5 13 8 13C3.5 13 1 8 1 8Z" stroke="currentColor" stroke-width="1.3"/><circle cx="8" cy="8" r="2" stroke="currentColor" stroke-width="1.3"/></svg>';
    });
  });

  /* ============ PASSWORD STRENGTH ============ */
  const regPass = document.getElementById('regPass');
  const bars = document.querySelectorAll('#strengthBars .strength-bar');
  const strengthText = document.getElementById('strengthText');

  function scorePassword(pw) {
    let score = 0;
    if (pw.length >= 6) score++;
    if (pw.length >= 10) score++;
    if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    return Math.min(score, 4);
  }

  regPass.addEventListener('input', () => {
    const pw = regPass.value;
    const score = pw.length === 0 ? 0 : Math.max(1, scorePassword(pw));
    const colors = ['#e3e0da', '#8a2f2f', '#8a6a1f', '#3d7a5c', '#2f6b4f'];
    const labels = ['', 'Yếu', 'Trung bình', 'Khá mạnh', 'Mạnh'];
    bars.forEach((b, i) => {
      b.style.background = i < score ? colors[score] : 'var(--border)';
    });
    if (pw.length === 0) {
      strengthText.textContent = 'Nhập mật khẩu để kiểm tra độ mạnh';
    } else {
      strengthText.textContent = 'Độ mạnh: ' + labels[score];
    }
  });

  /* ============ FORM VALIDATION HELPERS ============ */
  function isEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }
  function setError(id, on) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('on', on);
  }

  /* ============ LOGIN SUBMIT ============ */
  const loginForm = document.getElementById('loginForm');
  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail');
    const pass = document.getElementById('loginPass');
    let ok = true;

    if (!isEmail(email.value.trim())) { setError('loginEmailErr', true); email.classList.add('invalid'); ok = false; }
    else { setError('loginEmailErr', false); email.classList.remove('invalid'); }

    if (pass.value.length < 6) { setError('loginPassErr', true); pass.classList.add('invalid'); ok = false; }
    else { setError('loginPassErr', false); pass.classList.remove('invalid'); }

    if (!ok) return;

    showLoading(true);

    fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value.trim(), password: pass.value })
    })
      .then(res => res.json())
      .then(data => {
        showLoading(false);
        if (data.success) {
          showToast(data.message);
          setTimeout(() => { window.location.href = data.redirect_url || '/home'; }, 1000);
        } else {
          setError('loginPassErr', true);
          document.getElementById('loginPassErr').textContent = data.message;
          pass.classList.add('invalid');
        }
      })
      .catch(err => {
        showLoading(false);
        showToast('Đã xảy ra lỗi hệ thống, vui lòng thử lại.');
      });
  });

  /* ============ REGISTER SUBMIT ============ */
  const registerForm = document.getElementById('registerForm');
  registerForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('regName');
    const email = document.getElementById('regEmail');
    const pass = document.getElementById('regPass');
    const terms = document.getElementById('regTerms');
    let ok = true;

    const nameVal = name.value.trim();
    if (nameVal.length < 2) { setError('regNameErr', true); name.classList.add('invalid'); ok = false; }
    else { setError('regNameErr', false); name.classList.remove('invalid'); }

    if (!isEmail(email.value.trim())) { setError('regEmailErr', true); email.classList.add('invalid'); ok = false; }
    else { setError('regEmailErr', false); email.classList.remove('invalid'); }

    if (pass.value.length < 6) { setError('regPassErr', true); pass.classList.add('invalid'); ok = false; }
    else { setError('regPassErr', false); pass.classList.remove('invalid'); }

    if (!terms.checked) { setError('regTermsErr', true); ok = false; }
    else { setError('regTermsErr', false); }

    if (!ok) return;

    showLoading(true);

    fetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: name.value.trim(),
        email: email.value.trim(),
        password: pass.value,
        terms: terms.checked
      })
    })
      .then(res => res.json())
      .then(data => {
        showLoading(false);
        if (data.success) {
          showToast(data.message);
          setTimeout(() => { switchTab('login'); }, 1400);
        } else {
          setError('regEmailErr', true);
          document.getElementById('regEmailErr').textContent = data.message;
          email.classList.add('invalid');
        }
      })
      .catch(err => {
        showLoading(false);
        showToast('Đã xảy ra lỗi hệ thống, vui lòng thử lại.');
      });
  });


  /* ============ FORGOT SUBMIT ============ */
  const forgotForm = document.getElementById('forgotForm');
  forgotForm.addEventListener('submit', (e) => {
    e.preventDefault();
    showToast('Tính năng đang phát triển');
  });

  /* ============ GOOGLE OAUTH ============ */
  document.getElementById('googleLogin').addEventListener('click', () => {
    window.location.href = '/auth/google/login';
  });
  document.getElementById('googleRegister').addEventListener('click', () => {
    window.location.href = '/auth/google/login';
  });

  /* ============ TOAST ============ */
  const toast = document.getElementById('toast');
  const toastMsg = document.getElementById('toastMsg');
  let toastTimer;
  function showToast(msg) {
    toastMsg.textContent = msg;
    toast.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('on'), 3000);
  }

  /* ============ CLEAR ERRORS ON INPUT ============ */
  document.querySelectorAll('input').forEach(inp => {
    inp.addEventListener('input', () => {
      inp.classList.remove('invalid');
      const err = inp.parentElement.querySelector('.field-error') || inp.closest('.field')?.querySelector('.field-error');
      if (err) err.classList.remove('on');
    });
  });

})();
