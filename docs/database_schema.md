# Hướng Dẫn Thiết Kế Cấu Trúc Cơ Sở Dữ Liệu (Database Schema)

Để hệ thống hoạt động ổn định, bảo toàn tính toàn vẹn dữ liệu (không bị thất thoát tiền, không bị trùng lặp giao dịch), dự án TRAMTUONGTAC nên sử dụng hệ quản trị CSDL quan hệ (Relational Database) như **PostgreSQL** hoặc **MySQL**, kết hợp với ORM là **SQLAlchemy**.

Dưới đây là thiết kế các bảng (Tables) cốt lõi của hệ thống.

## 1. Khối Quản Lý Người Dùng & Phân Quyền

### Bảng `users`
Lưu trữ thông tin đăng nhập và số dư của người dùng.
- `id`: Integer (Primary Key, Auto Increment)
- `email`: String (Unique, Indexed)
- `password_hash`: String
- `full_name`: String
- `balance`: Decimal / Numeric (Lưu số dư Credits, không được dùng Float để tránh sai số)
- `role`: Enum ('USER', 'ADMIN') - Quyền hạn
- `is_active`: Boolean (Trạng thái bị khóa hay không)
- `created_at`: DateTime
- `updated_at`: DateTime

### Bảng `social_accounts`
Lưu trữ các tài khoản mạng xã hội (Facebook, TikTok) mà user liên kết để làm nhiệm vụ.
- `id`: Integer (Primary Key)
- `user_id`: Integer (Foreign Key -> users.id)
- `platform`: Enum ('FACEBOOK', 'TIKTOK', 'INSTAGRAM')
- `social_id`: String (ID UID của nền tảng)
- `profile_url`: String
- `status`: Enum ('PENDING', 'ACTIVE', 'BLOCKED') (Chờ duyệt, đã duyệt, bị admin khóa)
- `is_selected`: Boolean (Được user chọn làm tài khoản mặc định đi thực hiện nhiệm vụ)
- `is_deleted`: Boolean (Soft delete)
- `created_at`: DateTime

## 2. Khối Nhiệm Vụ (Jobs & Tasks)

### Bảng `jobs`
Lưu thông tin một gói nhiệm vụ do người dùng (Advertiser) tạo ra (Ví dụ: "Tăng 1000 like bài viết X").
- `id`: Integer (Primary Key)
- `user_id`: Integer (Người tạo nhiệm vụ)
- `platform`: Enum ('FACEBOOK', 'TIKTOK')
- `action_type`: Enum ('LIKE', 'FOLLOW', 'COMMENT', 'SHARE')
- `target_url`: String (Link cần tăng tương tác)
- `quantity`: Integer (Số lượng cần mua, ví dụ 1000)
- `current_count`: Integer (Số lượng đã hoàn thành)
- `price_per_action`: Decimal (Giá trả cho 1 lần tương tác)
- `total_cost`: Decimal (Tổng tiền = quantity * price_per_action)
- `status`: Enum ('RUNNING', 'COMPLETED', 'CANCELED')
- `is_deleted`: Boolean (Soft delete)
- `created_at`: DateTime
- `updated_at`: DateTime

### Bảng `tasks`
Lưu trữ lịch sử thực hiện nhiệm vụ của người dùng (Worker) đi cày thuê.
- `id`: Integer (Primary Key)
- `job_id`: Integer (Foreign Key -> jobs.id)
- `worker_id`: Integer (Foreign Key -> users.id) (Người làm nhiệm vụ)
- `social_account_id`: Integer (Foreign Key -> social_accounts.id) (Làm bằng clone nào)
- `reward`: Decimal (Tiền công nhận được)
- `status`: Enum ('PENDING', 'VERIFIED', 'REJECTED') (Đang chờ hệ thống check, hoặc admin duyệt)
- `completed_at`: DateTime
- `is_deleted`: Boolean (Soft delete)
- `created_at`: DateTime

## 3. Khối Tài Chính (Giao dịch)

### Bảng `transactions`
Lưu vết 100% dòng tiền ra/vào hệ thống (Nạp tiền, rút tiền, trừ tiền tạo Job, cộng tiền làm Task).
- `id`: Integer (Primary Key)
- `user_id`: Integer (Foreign Key -> users.id)
- `amount`: Decimal (Số tiền, có thể âm hoặc dương)
- `type`: Enum ('DEPOSIT', 'WITHDRAW', 'CREATE_JOB', 'TASK_REWARD', 'REFUND')
- `status`: Enum ('PENDING', 'SUCCESS', 'FAILED')
- `reference_code`: String (Mã giao dịch ngân hàng / MoMo nếu có)
- `description`: String (Ghi chú)
- `created_at`: DateTime

## 4. Khối Hệ Thống (Logs & Config)

### Bảng `action_logs`
Lưu trữ nhật ký các hoạt động quan trọng trong hệ thống (như Admin sửa cấu hình, cảnh báo spam).
- `id`: Integer (Primary Key, Auto Increment)
- `user_id`: Integer (Có thể null nếu là log do hệ thống tự sinh)
- `type`: Enum ('admin', 'system', 'user') - Phân loại nguồn tạo ra log
- `action`: String (Tên hành động ngắn gọn)
- `details`: Text (Chi tiết sự kiện, giá trị cũ/mới)
- `ip_address`: String (IP người thực hiện)
- `created_at`: DateTime

## 5. Các Lưu Ý Về Database (Best Practices)

1. **ACID Transactions**: Mọi thao tác đụng đến tiền (Ví dụ: User bấm Tạo Nhiệm Vụ -> Trừ tiền trong `users` + Tạo record trong `jobs` + Tạo record trong `transactions`) PHẢI được bọc trong một Database Transaction (`db.session.commit()` một lần duy nhất). Nếu 1 trong 3 bước lỗi, phải `db.session.rollback()` toàn bộ.
2. **Indexing (Đánh chỉ mục)**: Cần tạo Index cho các cột thường xuyên tìm kiếm hoặc dùng làm khóa ngoại như `users.email`, `jobs.status`, `transactions.user_id`, `transactions.type`, `transactions.status`, `tasks.job_id`, `tasks.worker_id`, `tasks.social_account_id`, và `tasks.status`.
3. **Kiểu dữ liệu tiền tệ**: Tuyệt đối không dùng kiểu `Float` hay `Real` để lưu tiền (vì sai số nhị phân). Hãy dùng `Numeric(15, 2)` (PostgreSQL) hoặc `Decimal`. Khi tính toán lưu ý phải đưa về cùng kiểu (float hoặc Decimal).
4. **Soft Delete**: Hạn chế dùng lệnh `DELETE` record trong DB. Thêm cột `is_deleted = Boolean` để ẩn dữ liệu (Soft delete) nhằm giữ lại lịch sử đối soát sau này.
5. **Relationships (ORM)**: Thiết lập sẵn các `db.relationship` với `lazy='dynamic'` để có thể trực tiếp query qua liên kết (ví dụ: `current_user.social_accounts.filter_by(...)`) mà không cần join thủ công ở Controller, giúp tối ưu và làm sạch code ở View/Template.
