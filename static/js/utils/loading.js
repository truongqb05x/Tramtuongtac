window.showLoading = function(show) {
    const loader = document.getElementById('globalLoading');
    if (loader) {
      if (show) loader.classList.add('active');
      else loader.classList.remove('active');
    }
};

// Hiệu ứng loading lúc mới vào trang
document.addEventListener("DOMContentLoaded", () => {
    const loaderText = document.querySelector('#globalLoading .loading-text');
    if (loaderText) {
        // Lưu lại text gốc (tuỳ chọn) hoặc đổi luôn
        loaderText.dataset.originalText = loaderText.textContent;
        loaderText.textContent = 'Vui lòng chờ...';
    }
    window.showLoading(true);
});

window.addEventListener("load", () => {
    // Thêm một chút delay nhỏ để loading nhìn mượt hơn
    setTimeout(() => {
        window.showLoading(false);
        // Khôi phục text gốc nếu cần sau khi ẩn
        const loaderText = document.querySelector('#globalLoading .loading-text');
        if (loaderText && loaderText.dataset.originalText) {
            loaderText.textContent = loaderText.dataset.originalText;
        }
    }, 500);
});