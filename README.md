# Hệ thống quản lý Ký túc xá sinh viên (Project 2 – Yêu cầu 3)

Web app **Flask + MySQL** xây dựng trên CSDL trong `database/KTXSV.sql` (bảng, trigger, dữ liệu mẫu).
Giao diện tiếng Việt, người dùng không cần biết lập trình vẫn sử dụng được.

## Tính năng

**Quản lý dữ liệu (thêm / sửa / xóa / tìm kiếm)**
- Sinh viên · Phòng ở (hiển thị số người đang ở và chỗ trống) · Khách đến thăm
- Danh mục dịch vụ · Nhật ký sử dụng dịch vụ (thành tiền = đơn giá × số lượng, tự tính)
- Xe vé tháng (tối đa 2 xe/sinh viên) · Lượt gửi/lấy xe (2 lượt miễn phí/ngày, từ lượt 3 phụ phí 3.000đ – tự tính)

**4 báo cáo theo đề bài**
1. **Hóa đơn hàng tháng** – tiền phòng (tính chẵn tháng) + dịch vụ + vé xe tháng + phụ phí gửi xe, xem theo danh sách hoặc từng người (trang chi tiết, có nút **In hóa đơn**).
2. **Dịch vụ theo khoảng ngày** – tên dịch vụ và tổng tiền mỗi dịch vụ của sinh viên từ ngày … đến ngày …
3. **Khách đến thăm** – theo **tuần** hoặc **tháng**, kèm số lần mỗi khách đến chơi và các ngày đến.
4. **Doanh thu dịch vụ** – từng dịch vụ theo 12 tháng, có biểu đồ.

**Tính năng phụ:** bảng điều khiển (thống kê, mức lấp đầy phòng), tìm kiếm, xuất CSV (mở được bằng Excel) cho cả 4 báo cáo, in hóa đơn, kiểm tra ràng buộc nghiệp vụ (phòng đầy, quá 2 xe…) kèm thông báo lỗi dễ hiểu.

## Cài đặt & chạy

Yêu cầu: **Python 3.9+** và **MySQL 8.0.13+** (file SQL dùng `DEFAULT (CURRENT_DATE)` và `CHECK`).

```bash
# 1. Cài thư viện
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Cấu hình kết nối MySQL (đổi theo máy của bạn)
export DB_HOST=localhost DB_USER=root DB_PASSWORD=mat_khau DB_NAME=ktx
#   Windows PowerShell:  $env:DB_PASSWORD="mat_khau"

# 3. Tạo CSDL + bảng + trigger + dữ liệu mẫu (đọc từ database/KTXSV.sql)
python init_db.py            # thêm --reset để xóa và tạo lại từ đầu

# 4. Chạy web
python app.py                # mở http://127.0.0.1:5000
```

> Nếu MySQL báo lỗi khi tạo trigger (`log_bin_trust_function_creators`), chạy với tài khoản root hoặc thực hiện
> `SET GLOBAL log_bin_trust_function_creators = 1;`
>
> Bạn cũng có thể tự chạy thẳng `database/KTXSV.sql` trong MySQL Workbench thay cho bước 3 (nhớ `CREATE DATABASE ktx; USE ktx;` trước).

## Cấu trúc thư mục

```
ktx-app/
├── app.py              # Flask: CRUD + 4 báo cáo + bảng điều khiển
├── init_db.py          # nạp database/KTXSV.sql vào MySQL
├── database/KTXSV.sql  # CSDL (Yêu cầu 2)
├── templates/          # giao diện HTML (Jinja2 + Bootstrap 5)
├── static/style.css
└── requirements.txt
```

## Ghi chú thiết kế

- Tiền phòng tính chẵn tháng: sinh viên có phòng và `NgayBatDauO` ≤ ngày cuối tháng thì phải trả đủ tiền phòng tháng đó.
- Vé xe tháng tính cho xe đang hiệu lực, đăng ký trước hoặc trong tháng.
- Trigger MySQL vẫn là nơi bảo vệ dữ liệu chính; app kiểm tra thêm khi **sửa** (trigger gốc chỉ chạy khi INSERT) và tự đánh số lại lượt gửi xe trong ngày khi sửa/xóa lượt.
- Trang web dùng CDN cho Bootstrap/Chart.js nên cần Internet khi mở giao diện.

## Đưa lên GitHub

```bash
git init && git add . && git commit -m "KTX management app"
git branch -M main
git remote add origin https://github.com/<ten-ban>/<ten-repo>.git
git push -u origin main
```
