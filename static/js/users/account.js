(function(){
  'use strict';

  /* ============ PASSWORD STRENGTH ============ */
  const newPass = document.getElementById('newPass');
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

  if (newPass) {
    newPass.addEventListener('input', () => {
      const pw = newPass.value;
      const score = pw.length === 0 ? 0 : Math.max(1, scorePassword(pw));
      const colors = ['#e3e0da', '#8a2f2f', '#8a6a1f', '#3d7a5c', '#2f6b4f'];
      const labels = ['', 'Yếu', 'Trung bình', 'Khá mạnh', 'Mạnh'];
      bars.forEach((b, i) => {
        b.style.background = i < score ? colors[score] : 'var(--border)';
      });
      strengthText.textContent = pw.length === 0
        ? 'Nhập mật khẩu để kiểm tra độ mạnh'
        : 'Độ mạnh: ' + labels[score];
    });
  }

  document.getElementById('changePassBtn').addEventListener('click', async () => {
    const cur = document.getElementById('currentPass').value;
    const np = document.getElementById('newPass').value;
    const cp = document.getElementById('confirmPass').value;
    const btn = document.getElementById('changePassBtn');
    
    if (!cur) { showToast('Vui lòng nhập mật khẩu hiện tại.'); return; }
    if (np.length < 6) { showToast('Mật khẩu mới tối thiểu 6 ký tự.'); return; }
    if (np !== cp) { showToast('Mật khẩu nhập lại không khớp.'); return; }
    
    btn.disabled = true;
    btn.textContent = 'Đang xử lý...';
    
    showLoading(true);

    try {
      const res = await fetch('/settings/account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_pass: cur, new_pass: np })
      });
      const data = await res.json();
      
      showToast(data.message);
      
      if (data.success) {
        document.getElementById('currentPass').value = '';
        document.getElementById('newPass').value = '';
        document.getElementById('confirmPass').value = '';
        bars.forEach(b => b.style.background = 'var(--border)');
        strengthText.textContent = 'Nhập mật khẩu để kiểm tra độ mạnh';
      }
    } catch (err) {
      showToast('Lỗi kết nối máy chủ.');
    } finally {
      showLoading(false);
      btn.disabled = false;
      btn.textContent = 'Đổi mật khẩu';
    }
  });


})();