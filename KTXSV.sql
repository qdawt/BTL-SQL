-- ============================================================================
-- HỆ THỐNG QUẢN LÝ KÝ TÚC XÁ SINH VIÊN
-- RDBMS: PostgreSQL / MySQL (Cú pháp tương thích chuẩn ANSI SQL)
-- ============================================================================

-- 1. TẠO CÁC BẢNG CƠ SỞ (BASE TABLES)

-- Bảng Phòng ở
CREATE TABLE Phong (
    MaPhong VARCHAR(10) PRIMARY KEY,
    SoPhong VARCHAR(10) NOT NULL UNIQUE,
    LoaiPhong VARCHAR(50) NOT NULL,
    DonGia DECIMAL(12, 2) NOT NULL CHECK (DonGia >= 0),
    SoNguoiToiDa INT NOT NULL CHECK (SoNguoiToiDa > 0)
);

-- Bảng Sinh viên
CREATE TABLE SinhVien (
    MaSV VARCHAR(20) PRIMARY KEY,
    SoCMT VARCHAR(20) NOT NULL UNIQUE,
    HoTen VARCHAR(100) NOT NULL,
    NgaySinh DATE NOT NULL,
    Lop VARCHAR(50) NOT NULL,
    QueQuan VARCHAR(200) NOT NULL,
    MaPhong VARCHAR(10),
    NgayBatDauO DATE,
    FOREIGN KEY (MaPhong) REFERENCES Phong(MaPhong) ON DELETE SET NULL
);

-- Bảng Khách đến thăm KTX
CREATE TABLE KhachTham (
    MaKhach INT AUTO_INCREMENT PRIMARY KEY,
    SoCMT VARCHAR(20) NOT NULL,
    HoTen VARCHAR(100) NOT NULL,
    NgaySinh DATE,
    MaSV VARCHAR(20) NOT NULL,
    NgayDenChoi DATE NOT NULL,
    FOREIGN KEY (MaSV) REFERENCES SinhVien(MaSV) ON DELETE CASCADE
);

-- Bảng Danh mục Dịch vụ chung (Giặt là, Ăn uống, Cho thuê xe...)
CREATE TABLE DichVu (
    MaDV VARCHAR(10) PRIMARY KEY,
    TenDV VARCHAR(100) NOT NULL,
    DonGia DECIMAL(12, 2) NOT NULL CHECK (DonGia >= 0)
);

-- Bảng Nhật ký Sử dụng Dịch vụ chung của Sinh viên
CREATE TABLE SuDungDichVu (
    MaSDDV INT AUTO_INCREMENT PRIMARY KEY,
    MaSV VARCHAR(20) NOT NULL,
    MaDV VARCHAR(10) NOT NULL,
    ThoiGianSuDung DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    SoLuong INT NOT NULL DEFAULT 1 CHECK (SoLuong > 0),
    ThanhTien DECIMAL(12, 2) NOT NULL CHECK (ThanhTien >= 0),
    FOREIGN KEY (MaSV) REFERENCES SinhVien(MaSV) ON DELETE CASCADE,
    FOREIGN KEY (MaDV) REFERENCES DichVu(MaDV) ON DELETE CASCADE
);

-- 2. QUẢN LÝ DỊCH VỤ GỬI XE VÉ THÁNG

-- Bảng Thẻ xe vé tháng sinh viên đăng ký (Max 2 xe/SV)
CREATE TABLE XeThang (
    MaXeThang VARCHAR(20) PRIMARY KEY,
    MaSV VARCHAR(20) NOT NULL,
    BienSoXe VARCHAR(20) NOT NULL,
    LoaiXe VARCHAR(50) NOT NULL,
    NgayDangKy DATE NOT NULL DEFAULT (CURRENT_DATE),
    GiaVeThang DECIMAL(12, 2) NOT NULL DEFAULT 100000.00,
    TrangThai BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (MaSV) REFERENCES SinhVien(MaSV) ON DELETE CASCADE
);

-- Bảng Lượt Gửi/Lấy Xe Vé Tháng (Định lượng phí phát sinh từ lượt thứ 3 trong ngày)
CREATE TABLE LuotGuiXe (
    MaLuot INT AUTO_INCREMENT PRIMARY KEY,
    MaXeThang VARCHAR(20) NOT NULL,
    ThoiGianVao DATETIME NOT NULL,
    ThoiGianRa DATETIME,
    NgayGiaoDich DATE NOT NULL,
    SoLieuLuotTrongNgay INT NOT NULL DEFAULT 1,
    PhuPhiPhatSinh DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (MaXeThang) REFERENCES XeThang(MaXeThang) ON DELETE CASCADE
);

-- 3. RÀNG BUỘC NGHIỆP VỤ (TRIGGERS)

-- RÀNG BUỘC 1: Kiểm tra số lượng người tối đa trong phòng khi thêm Sinh Viên
DELIMITER //
CREATE TRIGGER trg_Check_SoNguoi_Phong
BEFORE INSERT ON SinhVien
FOR EACH ROW
BEGIN
    DECLARE v_SoHienTai INT;
    DECLARE v_SoToiDa INT;

    IF NEW.MaPhong IS NOT NULL THEN
        SELECT COUNT(*) INTO v_SoHienTai FROM SinhVien WHERE MaPhong = NEW.MaPhong;
        SELECT SoNguoiToiDa INTO v_SoToiDa FROM Phong WHERE MaPhong = NEW.MaPhong;

        IF v_SoHienTai >= v_SoToiDa THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Lỗi: Phòng đã đạt số lượng người ở tối đa!';
        END IF;
    END IF;
END;
//
DELIMITER ;

-- RÀNG BUỘC 2: Mỗi sinh viên chỉ được đăng ký tối đa 2 xe vé tháng
DELIMITER //
CREATE TRIGGER trg_Check_SoXeThang_SinhVien
BEFORE INSERT ON XeThang
FOR EACH ROW
BEGIN
    DECLARE v_SoXeHienTai INT;

    SELECT COUNT(*) INTO v_SoXeHienTai 
    FROM XeThang 
    WHERE MaSV = NEW.MaSV AND TrangThai = TRUE;

    IF v_SoXeHienTai >= 2 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Lỗi: Mỗi sinh viên chỉ được đăng ký tối đa 2 xe vé tháng!';
    END IF;
END;
//
DELIMITER ;

-- RÀNG BUỘC 3: Tự động tính lượt gửi/lấy trong ngày và phụ phí 3.000 VNĐ từ lượt 3 trở đi
DELIMITER //
CREATE TRIGGER trg_TinhPhi_LuotGuiXe
BEFORE INSERT ON LuotGuiXe
FOR EACH ROW
BEGIN
    DECLARE v_LuotTrongNgay INT;

    SELECT COUNT(*) + 1 INTO v_LuotTrongNgay
    FROM LuotGuiXe
    WHERE MaXeThang = NEW.MaXeThang AND NgayGiaoDich = NEW.NgayGiaoDich;

    SET NEW.SoLieuLuotTrongNgay = v_LuotTrongNgay;

    IF v_LuotTrongNgay > 2 THEN
        SET NEW.PhuPhiPhatSinh = 3000.00;
    ELSE
        SET NEW.PhuPhiPhatSinh = 0.00;
    END IF;
END;
//
DELIMITER ;


-- 4. TRUY VẤN THEO YÊU CẦU ĐỀ BÀI


-- TRUY VẤN 1: Bảng tổng hợp chi phí phòng & tất cả dịch vụ hàng tháng của từng SV
-- (Tiền phòng tính chẵn tháng + Tiền DV chung + Tiền xe tháng + Phụ phí gửi xe quá lượt)
SELECT 
    sv.MaSV,
    sv.HoTen,
    sv.Lop,
    COALESCE(p.SoPhong, 'Chưa xếp') AS SoPhong,
    MONTH(CURRENT_DATE) AS Thang,
    YEAR(CURRENT_DATE) AS Nam,
    COALESCE(p.DonGia, 0) AS TienPhong,
    COALESCE(TienDV.TongTienDV, 0) AS TienDichVuChung,
    COALESCE(TienXeThang.TongGiaVeXe, 0) AS TienVeXeThang,
    COALESCE(PhuPhiXe.TongPhuPhi, 0) AS PhuPhiGuiXe,
    (
        COALESCE(p.DonGia, 0) + 
        COALESCE(TienDV.TongTienDV, 0) + 
        COALESCE(TienXeThang.TongGiaVeXe, 0) + 
        COALESCE(PhuPhiXe.TongPhuPhi, 0)
    ) AS TongHoaDonThang
FROM SinhVien sv
LEFT JOIN Phong p ON sv.MaPhong = p.MaPhong
LEFT JOIN (
    SELECT MaSV, SUM(ThanhTien) AS TongTienDV
    FROM SuDungDichVu
    WHERE MONTH(ThoiGianSuDung) = MONTH(CURRENT_DATE) 
      AND YEAR(ThoiGianSuDung) = YEAR(CURRENT_DATE)
    GROUP BY MaSV
) TienDV ON sv.MaSV = TienDV.MaSV
LEFT JOIN (
    SELECT MaSV, SUM(GiaVeThang) AS TongGiaVeXe
    FROM XeThang
    WHERE TrangThai = TRUE
    GROUP BY MaSV
) TienXeThang ON sv.MaSV = TienXeThang.MaSV
LEFT JOIN (
    SELECT xt.MaSV, SUM(lg.PhuPhiPhatSinh) AS TongPhuPhi
    FROM LuotGuiXe lg
    JOIN XeThang xt ON lg.MaXeThang = xt.MaXeThang
    WHERE MONTH(lg.NgayGiaoDich) = MONTH(CURRENT_DATE) 
      AND YEAR(lg.NgayGiaoDich) = YEAR(CURRENT_DATE)
    GROUP BY xt.MaSV
) PhuPhiXe ON sv.MaSV = PhuPhiXe.MaSV;

-- TRUY VẤN 2: Thống kê tổng tiền từng loại dịch vụ mà SV đã dùng trong khoảng thời gian [Từ ngày - Đến ngày]
-- (Thay biến '2026-10-01' và '2026-10-31' theo khoảng thời gian tùy chọn)
SELECT 
    sv.MaSV,
    sv.HoTen,
    dv.TenDV,
    SUM(sd.SoLuong) AS TongSoLuong,
    SUM(sd.ThanhTien) AS TongTienDichVu
FROM SinhVien sv
JOIN SuDungDichVu sd ON sv.MaSV = sd.MaSV
JOIN DichVu dv ON sd.MaDV = dv.MaDV
WHERE sd.ThoiGianSuDung BETWEEN '2026-10-01 00:00:00' AND '2026-10-31 23:59:59'
GROUP BY sv.MaSV, sv.HoTen, dv.TenDV;


-- TRUY VẤN 3: Danh sách khách đến thăm từng SV kèm số lần ghé thăm theo Tháng (hoặc Tuần)
SELECT 
    sv.MaSV,
    sv.HoTen AS TenSinhVien,
    kt.SoCMT AS CMT_Khach,
    kt.HoTen AS TenKhach,
    COUNT(kt.MaKhach) AS SoLanDenChoi
FROM SinhVien sv
JOIN KhachTham kt ON sv.MaSV = kt.MaSV
WHERE MONTH(kt.NgayDenChoi) = MONTH(CURRENT_DATE) 
  AND YEAR(kt.NgayDenChoi) = YEAR(CURRENT_DATE)
GROUP BY sv.MaSV, sv.HoTen, kt.SoCMT, kt.HoTen;

-- 5. SAMPLE DỮ LIỆU

-- TRUY VẤN 4: Danh mục dịch vụ cùng tổng doanh thu hàng tháng trong KTX
SELECT 
    dv.MaDV,
    dv.TenDV,
    MONTH(sd.ThoiGianSuDung) AS Thang,
    YEAR(sd.ThoiGianSuDung) AS Nam,
    SUM(sd.ThanhTien) AS DoanhThu
FROM DichVu dv
LEFT JOIN SuDungDichVu sd ON dv.MaDV = sd.MaDV
GROUP BY dv.MaDV, dv.TenDV, MONTH(sd.ThoiGianSuDung), YEAR(sd.ThoiGianSuDung)
ORDER BY Nam DESC, Thang DESC;

-- 1. Thêm dữ liệu Phòng ở
INSERT INTO Phong (MaPhong, SoPhong, LoaiPhong, DonGia, SoNguoiToiDa) VALUES
('P101', '101', 'Phòng 4 người (Điều hòa)', 1200000.00, 4),
('P102', '102', 'Phòng 6 người (Quạt)', 800000.00, 6),
('P201', '201', 'Phòng 2 người (VIP)', 2000000.00, 2);

-- 2. Thêm dữ liệu Sinh viên
INSERT INTO SinhVien (MaSV, SoCMT, HoTen, NgaySinh, Lop, QueQuan, MaPhong, NgayBatDauO) VALUES
('SV001', '001202001111', 'Nguyễn Văn An', '2004-05-15', 'CNTT1-K17', 'Hà Nội', 'P101', '2024-09-01'),
('SV002', '001202002222', 'Trần Thị Bình', '2004-08-20', 'ATTT2-K17', 'Nam Định', 'P101', '2024-09-01'),
('SV003', '001202003333', 'Lê Hoàng Cường', '2005-02-10', 'DVT1-K18', 'Hải Phòng', 'P102', '2025-09-01'),
('SV004', '001202004444', 'Phạm Minh Đức', '2005-11-05', 'CNTT2-K18', 'Nghệ An', 'P201', '2025-09-01');

-- 3. Thêm dữ liệu Khách đến thăm
INSERT INTO KhachTham (SoCMT, HoTen, NgaySinh, MaSV, NgayDenChoi) VALUES
('001199005555', 'Nguyễn Văn Nam', '1980-01-01', 'SV001', '2026-10-05'),
('001199006666', 'Trần Văn Hùng', '1978-04-12', 'SV002', '2026-10-10');

-- 4. Thêm Danh mục Dịch vụ
INSERT INTO DichVu (MaDV, TenDV, DonGia) VALUES
('DV01', 'Giặt là', 15000.00),
('DV02', 'Ăn sáng / Cơm ca', 30000.00),
('DV03', 'Cho thuê xe đạp', 20000.00),
('DV04', 'Rửa xe', 25000.00);

-- 5. Nhật ký Sử dụng Dịch vụ (Tháng 10/2026)
INSERT INTO SuDungDichVu (MaSV, MaDV, ThoiGianSuDung, SoLuong, ThanhTien) VALUES
('SV001', 'DV01', '2026-10-05 08:30:00', 3, 45000.00),   -- 3 lượt giặt = 45k
('SV001', 'DV02', '2026-10-10 12:00:00', 5, 150000.00),  -- 5 suất ăn = 150k
('SV002', 'DV01', '2026-10-06 09:15:00', 2, 30000.00),   -- 2 lượt giặt = 30k
('SV002', 'DV03', '2026-10-12 14:00:00', 1, 20000.00),   -- Thuê xe đạp = 20k
('SV003', 'DV02', '2026-10-15 18:30:00', 10, 300000.00), -- 10 suất ăn = 300k
('SV004', 'DV04', '2026-10-08 10:00:00', 2, 50000.00);   -- 2 lần rửa xe = 50k

-- 6. Đăng ký Xe vé tháng (Tối đa 2 xe/SV - 100k/tháng)
INSERT INTO XeThang (MaXeThang, MaSV, BienSoXe, LoaiXe, NgayDangKy, GiaVeThang, TrangThai) VALUES
('XT01', 'SV001', '29-A1 123.45', 'Xe máy Wave', '2026-09-01', 100000.00, TRUE),
('XT02', 'SV001', '29-MD 888.88', 'Xe điện VinFast', '2026-09-15', 100000.00, TRUE), -- SV001 đăng ký 2 xe = 200k
('XT03', 'SV002', '18-B2 567.89', 'Xe máy Vision', '2026-09-01', 100000.00, TRUE);  -- SV002 đăng ký 1 xe = 100k

-- 7. Nhật ký Lượt gửi xe trong ngày (Định lượng miễn phí 2 lượt/ngày, lượt 3 trở đi phạt 3.000đ/lượt)
INSERT INTO LuotGuiXe (MaXeThang, ThoiGianVao, ThoiGianRa, NgayGiaoDich, SoLieuLuotTrongNgay, PhuPhiPhatSinh) VALUES
('XT01', '2026-10-10 07:00:00', '2026-10-10 09:00:00', '2026-10-10', 1, 0.00),    -- Lượt 1 (Miễn phí)
('XT01', '2026-10-10 10:00:00', '2026-10-10 12:00:00', '2026-10-10', 2, 0.00),    -- Lượt 2 (Miễn phí)
('XT01', '2026-10-10 13:00:00', '2026-10-10 15:00:00', '2026-10-10', 3, 3000.00), -- Lượt 3 (+3.000đ)
('XT01', '2026-10-10 17:00:00', '2026-10-10 21:00:00', '2026-10-10', 4, 3000.00); -- Lượt 4 (+3.000đ => Tổng phụ phí 6k)