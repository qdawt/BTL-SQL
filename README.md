
# 🏢 HỆ THỐNG QUẢN LÝ KÝ TÚC XÁ SINH VIÊN

**Project 2 – Môn Cơ sở dữ liệu**

Ứng dụng quản lý ký túc xá sinh viên được xây dựng nhằm hỗ trợ quản lý thông tin sinh viên, phòng ở, khách đến thăm, dịch vụ sinh hoạt và xe đăng ký gửi vé tháng.

Ứng dụng có giao diện tiếng Việt, hỗ trợ quản lý dữ liệu, kiểm tra các ràng buộc nghiệp vụ và tổng hợp chi phí theo tháng.

---

## 📌 1. Giới thiệu đề tài

Đề tài xây dựng hệ thống quản lý ký túc xá sinh viên với các mục tiêu:

- Quản lý thông tin sinh viên và phòng ở.
- Theo dõi khách đến thăm sinh viên.
- Quản lý danh mục và lịch sử sử dụng dịch vụ.
- Quản lý xe đăng ký vé tháng và các lượt gửi/lấy xe.
- Tự động tính toán chi phí và lập hóa đơn hàng tháng.
- Cung cấp các báo cáo phục vụ công tác quản lý ký túc xá.

## ✨ 2. Các chức năng chính

### 2.1. Quản lý sinh viên
- Thêm, sửa, xóa và tìm kiếm sinh viên.
- Lưu thông tin cá nhân: mã sinh viên, số CMT/CCCD, họ tên, ngày sinh, lớp và quê quán.
- Theo dõi phòng ở và thời gian bắt đầu ở.

### 2.2. Quản lý phòng ở
- Quản lý danh sách phòng.
- Theo dõi loại phòng, đơn giá và sức chứa tối đa.
- Hiển thị số người đang ở và số chỗ còn trống.
- Kiểm tra ràng buộc khi phòng đã đủ số người.

### 2.3. Quản lý khách đến thăm
- Lưu thông tin khách đến thăm.
- Ghi nhận sinh viên được thăm và ngày đến.
- Tra cứu lịch sử khách đến thăm.

### 2.4. Quản lý dịch vụ
- Quản lý danh mục dịch vụ và đơn giá.
- Ghi nhận các lần sinh viên sử dụng dịch vụ.
- Tự động tính thành tiền theo đơn giá và số lượng.

Các dịch vụ có thể bao gồm giặt là, trông xe, cho thuê xe và ăn uống.

### 2.5. Quản lý xe vé tháng
- Quản lý thông tin xe đăng ký vé tháng.
- Kiểm tra giới hạn tối đa 2 xe vé tháng trên mỗi sinh viên.
- Theo dõi lịch sử gửi và lấy xe.
- Hai lượt đầu tiên trong ngày được miễn phí.
- Từ lượt thứ ba, phụ phí được tính 3.000 đồng/lượt.

## 📊 3. Các báo cáo

Hệ thống hỗ trợ các báo cáo chính theo yêu cầu đề bài:

| STT | Báo cáo | Nội dung |
|---|---|---|
| 1 | Hóa đơn hàng tháng | Tổng hợp tiền phòng, dịch vụ, vé xe tháng và phụ phí gửi xe. |
| 2 | Dịch vụ theo khoảng ngày | Thống kê tên dịch vụ và tổng tiền từng dịch vụ mà sinh viên đã sử dụng. |
| 3 | Khách đến thăm | Thống kê khách đến thăm theo tuần hoặc tháng và số lần đến. |
| 4 | Doanh thu dịch vụ | Thống kê doanh thu từng dịch vụ theo tháng. |

Ngoài ra, ứng dụng còn hỗ trợ:
- Bảng điều khiển tổng quan.
- Tìm kiếm dữ liệu.
- Xuất báo cáo CSV.
- Xem và in hóa đơn.
- Thông báo khi vi phạm các ràng buộc nghiệp vụ.

## 🛠️ 4. Công nghệ sử dụng

| Công nghệ | Vai trò |
|---|---|
| Python | Xử lý nghiệp vụ và vận hành ứng dụng. |
| Flask | Xây dựng ứng dụng và xử lý các trang giao diện. |
| SQLite | Lưu trữ dữ liệu trong phiên bản ứng dụng hiện tại. |
| SQL | Thiết kế bảng, khóa, quan hệ và truy vấn dữ liệu. |
| HTML/CSS | Xây dựng giao diện người dùng. |
| Bootstrap | Hỗ trợ bố cục và trình bày giao diện. |
| PyWebView | Hiển thị ứng dụng trong cửa sổ desktop. |

## 📁 5. Cấu trúc thư mục

```text
BTL-SQL/
│
├── app.py
├── requirements.txt
├── README.md
│
├── database/
│   └── KTXSV.sql
│
├── templates/
│   └── Các tệp giao diện HTML
│
├── static/
│   └── Các tệp CSS và tài nguyên giao diện
│
├── build/
│   └── Tài nguyên phục vụ đóng gói
│
├── dist/
│   └── Các tệp ứng dụng đã đóng gói
│
├── app.spec
└── KTXManager.spec
```

## 💻 6. Cài đặt và chạy ứng dụng bằng Python

### Bước 1. Tải mã nguồn

```bash
git clone https://github.com/qdawt/BTL-SQL.git
cd BTL-SQL
```

Hoặc tải repository dưới dạng ZIP từ GitHub và giải nén.

### Bước 2. Tạo môi trường ảo

Windows PowerShell:

```powershell
python -m venv .venv
```

Kích hoạt môi trường:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Bước 3. Cài đặt thư viện

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu gặp lỗi thiếu thư viện `webview`, cài bổ sung:

```bash
pip install pywebview
```

### Bước 4. Khởi chạy ứng dụng

```bash
python app.py
```

Ứng dụng Flask sử dụng địa chỉ localhost:

```text
http://127.0.0.1:5000
```

Nếu chạy thông qua PyWebView, giao diện sẽ được hiển thị trong cửa sổ desktop.

## 🖥️ 7. Sử dụng ứng dụng EXE

Dự án có thư mục `dist` chứa các tệp phục vụ phiên bản đóng gói.

Các bước sử dụng:

1. Tải thư mục hoặc tệp ZIP chứa ứng dụng từ repository.
2. Giải nén toàn bộ nội dung vào một thư mục.
3. Giữ nguyên cấu trúc các tệp đi kèm.
4. Mở tệp EXE của ứng dụng.
5. Chờ giao diện khởi động và sử dụng các chức năng quản lý.

**Lưu ý:** Không nên chỉ sao chép riêng file EXE nếu bản đóng gói có các thư viện hoặc tài nguyên đi kèm.

## 🗄️ 8. Dữ liệu và cơ sở dữ liệu

Ứng dụng sử dụng cơ sở dữ liệu SQLite trong phiên bản chạy hiện tại.

Tệp CSDL được lưu tại:

```text
%APPDATA%\KTXManager\ktx.db
```

## 📋 9. Các quy tắc nghiệp vụ

- Tiền thuê phòng được tính tròn tháng.
- Thành tiền dịch vụ bằng đơn giá nhân số lượng sử dụng.
- Vé xe tháng có mức phí 100.000 đồng/tháng.
- Hai lượt gửi/lấy xe đầu tiên trong ngày được miễn phụ phí.
- Từ lượt thứ ba, mỗi lượt phát sinh 3.000 đồng.
- Mỗi sinh viên được đăng ký tối đa hai xe vé tháng.
- Không cho phép xếp sinh viên vượt quá sức chứa của phòng.
- Các dữ liệu liên quan phải đảm bảo tính hợp lệ và nhất quán.

## 👥 10. Thành viên thực hiện

| STT | Họ và tên |
|---|---|
| 1 | Đào Quang Đạt |
| 2 | Trịnh Văn Huy |
| 3 | Trần Hữu Bảo |s
| 4 | Nguyễn Vũ Tuấn Anh |


**Đề tài:** Xây dựng hệ thống quản lý ký túc xá sinh viên  
**Môn học:** Cơ sở dữ liệu  
**Năm thực hiện:** 2026
