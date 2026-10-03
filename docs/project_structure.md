# Hướng Dẫn Tổ Chức Cấu Trúc File Dự Án (Architecture & Directory Structure)

Để dự án TRAMTUONGTAC dễ dàng bảo trì và mở rộng khi số lượng người dùng tăng lên, mã nguồn cần được tổ chức theo mô hình **MVC (Model-View-Controller)** kết hợp với **Flask Blueprints** để module hóa các tính năng.

## 1. Cấu Trúc Thư Mục Tiêu Chuẩn

Dưới đây là sơ đồ cấu trúc thư mục tối ưu cho Backend (Python/Flask) và Frontend (HTML/JS/CSS):

```text
Tramtuongtac/
├── app/                        # Thư mục chính chứa mã nguồn Backend
│   ├── __init__.py             # Khởi tạo Flask app, cấu hình database, đăng ký blueprints
│   ├── config.py               # Chứa các cấu hình môi trường (Development, Production)
│   ├── extensions.py           # Khởi tạo các thư viện (SQLAlchemy, Migrate, Redis, JWT)
│   │
│   ├── models/                 # Chứa cấu trúc CSDL (Database Models)
│   │   ├── __init__.py
│   │   ├── user.py             # Model User, Role, SocialAccount
│   │   ├── job.py              # Model Job, Task
│   │   ├── transaction.py      # Model Payment, History
│   │   └── log.py              # Model ActionLog (Nhật ký hoạt động hệ thống)
│   │
│   ├── controllers/            # Xử lý logic route (Blueprints)
│   │   ├── __init__.py
│   │   ├── admin_ctrl.py       # Xử lý route /admin/...
│   │   ├── user_ctrl.py        # Xử lý route /user/...
│   │   └── api_ctrl.py         # Cung cấp RESTful API cho ứng dụng mobile/frontend SPA
│   │
│   ├── services/               # Chứa business logic phức tạp và cấu hình file
│   │   ├── payment_service.py  # Xử lý gọi API ngân hàng, cộng/trừ tiền
│   │   ├── job_service.py      # Xử lý logic duyệt nhiệm vụ, tính toán phân phối
│   │   ├── facebook.py         # Xử lý tương tác Facebook Graph API (Lấy ID, kiểm tra Like/Follow)
│   │   ├── system_cfg.py       # Quản lý cấu hình hệ thống (Maintenance, Safe mode, Fee)
│   │   └── platform_cfg.py     # Quản lý thiết lập các mạng xã hội và hoạt động tương tác
│   │
│   └── utils/                  # Chứa các hàm tiện ích dùng chung
│       ├── decorators.py       # @login_required, @admin_required
│       ├── helpers.py          # Format ngày tháng, tạo random token
│       └── validators.py       # Validate email, mật khẩu
│
├── instance/                   # Chứa các file dữ liệu cục bộ không lưu vào Git (database, json config)
│   ├── system.json             # Lưu trữ cấu hình hệ thống động (không làm cứng vào code)
│   └── platforms.json          # Lưu trữ giá cả, active/inactive nền tảng
├── static/                     # Thư mục Frontend Assets (Không thay đổi nhiều)
│   ├── css/                    # Modular CSS (base, layout, components, pages)
│   ├── js/
│   │   ├── api.js              # File JS chứa các hàm call API (fetch/axios) dùng chung
│   │   ├── admin/              # Script riêng cho giao diện Admin
│   │   └── user/               # Script riêng cho giao diện User
│   └── img/
│
├── templates/                  # Giao diện HTML (Jinja2)
│   ├── admin/                  # Giao diện trang quản trị
│   ├── user/                   # Giao diện người dùng
│   └── emails/                 # Các mẫu email HTML (Quên mật khẩu, Xác thực)
│
├── migrations/                 # Thư mục sinh tự động bởi Flask-Migrate (Alembic)
├── requirements.txt            # Khai báo các thư viện phụ thuộc (pip)
├── app.py                      # Điểm đầu vào (Entry point) để chạy ứng dụng
└── .env                        # Chứa các biến môi trường nhạy cảm (DB_URI, SECRET_KEY)
```

## 2. Cách Tổ Chức Frontend (JavaScript & CSS)

### CSS (Theo phương pháp BEM / Modular)
- **Base**: Reset CSS, biến màu sắc (`var(--ink)`), typography.
- **Layout**: Header, Footer, Sidebar.
- **Components**: Nút bấm (Button), thẻ thông báo (Toast), form nhập liệu (Input).
- **Pages**: Các file CSS ghi đè cho từng trang cụ thể (vd: `login.css`, `dashboard.css`).

### JavaScript
- Không nên viết JS nhúng thẳng vào file HTML (`<script>`). Nên tách ra file `.js` và gọi vào phần cuối của thẻ `<body>`.
- **Tách API calls**: Nên có một file `api.js` chuyên bọc (wrap) hàm `fetch()`. Ví dụ:
  ```javascript
  const api = {
    post: async (endpoint, data) => { ... },
    get: async (endpoint) => { ... }
  };
  ```
  Giúp dễ dàng thêm Header Bearer Token khi gọi API, quản lý lỗi tập trung.

## 3. Quy Trình Phát Triển (Best Practices)

1. **Tách biệt Logic và Route (Fat Models, Thin Controllers)**: Controller chỉ nên nhận Request, gọi qua Service hoặc Model để xử lý, sau đó trả về Response (JSON hoặc render HTML). Không viết quá nhiều code thuật toán, cộng trừ tiền trực tiếp trong Controller.
2. **Sử dụng Blueprints**: Không gộp tất cả route vào `app.py`. Chia ra làm `admin_bp`, `auth_bp`, `user_bp`.
3. **Biến môi trường**: Không được hardcode mật khẩu DB, API Key vào code. Bắt buộc dùng file `.env` và thư viện `python-dotenv`.
4. **Log Hệ Thống**: Dùng thư viện `logging` của Python thay cho `print()`. Ghi log ra file để dễ truy vết lỗi trên môi trường production.
