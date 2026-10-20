# -*- coding: utf-8 -*-
"""Ứng dụng Desktop Quản lý Ký túc xá sinh viên (Flask + SQLite + PyWebView).

Đóng gói PyInstaller:
    pyinstaller --noconsole --onefile --add-data "templates;templates" --add-data "static;static" app.py
"""
import csv
import datetime as dt
import io
import os
import sqlite3
import sys
import threading
from decimal import Decimal

import webview
from flask import (Flask, Response, abort, flash, g, redirect, render_template,
                   request)
from markupsafe import Markup, escape

# ----------------------------------------------------------------------------
# Cấu hình đường dẫn cho PyInstaller & Database (Giải pháp B: AppData)
# ----------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    # Nếu là file .exe đóng gói bằng PyInstaller
    BASE_DIR = os.path.dirname(sys.executable)
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    # Nếu chạy script .py bình thường
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__)

# Lưu trữ database tại thư mục AppData của người dùng (Solution B)
# Giúp dữ liệu luôn bền vững, tránh lỗi phân quyền UAC hoặc thư mục chỉ đọc.
APPDATA_DIR = os.path.join(os.environ.get('APPDATA', BASE_DIR), 'KTXManager')
os.makedirs(APPDATA_DIR, exist_ok=True)
DB_PATH = os.path.join(APPDATA_DIR, "ktx.db")

app.secret_key = os.environ.get("SECRET_KEY", "ktx-dev-secret-key")


# --- BƯỚC 2: HÀM TỰ ĐỘNG TẠO/SỬA DATABASE HOÀN CHỈNH ---
def init_db_if_not_exists():
    # Tự động tạo thư mục nếu chưa tồn tại
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    
    # Kiểm tra xem bảng SinhVien đã tồn tại chưa
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SinhVien';")
    if not cur.fetchone():
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS Phong (
            MaPhong TEXT PRIMARY KEY,
            SoPhong TEXT NOT NULL UNIQUE,
            LoaiPhong TEXT NOT NULL,
            DonGia DECIMAL(12, 2) NOT NULL CHECK (DonGia >= 0),
            SoNguoiToiDa INTEGER NOT NULL CHECK (SoNguoiToiDa > 0)
        );

        CREATE TABLE IF NOT EXISTS SinhVien (
            MaSV TEXT PRIMARY KEY,
            SoCMT TEXT NOT NULL UNIQUE,
            HoTen TEXT NOT NULL,
            NgaySinh TEXT NOT NULL,
            Lop TEXT NOT NULL,
            QueQuan TEXT NOT NULL,
            MaPhong TEXT,
            NgayBatDauO TEXT,
            FOREIGN KEY (MaPhong) REFERENCES Phong(MaPhong) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS KhachTham (
            MaKhach INTEGER PRIMARY KEY AUTOINCREMENT,
            SoCMT TEXT NOT NULL,
            HoTen TEXT NOT NULL,
            NgaySinh TEXT,
            MaSV TEXT NOT NULL,
            NgayDenChoi TEXT NOT NULL,
            FOREIGN KEY (MaSV) REFERENCES SinhVien(MaSV) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS DichVu (
            MaDV TEXT PRIMARY KEY,
            TenDV TEXT NOT NULL,
            DonGia DECIMAL(12, 2) NOT NULL CHECK (DonGia >= 0)
        );

        CREATE TABLE IF NOT EXISTS SuDungDichVu (
            MaSDDV INTEGER PRIMARY KEY AUTOINCREMENT,
            MaSV TEXT NOT NULL,
            MaDV TEXT NOT NULL,
            ThoiGianSuDung TEXT NOT NULL,
            SoLuong INTEGER NOT NULL DEFAULT 1 CHECK (SoLuong > 0),
            ThanhTien DECIMAL(12, 2) NOT NULL CHECK (ThanhTien >= 0),
            FOREIGN KEY (MaSV) REFERENCES SinhVien(MaSV) ON DELETE CASCADE,
            FOREIGN KEY (MaDV) REFERENCES DichVu(MaDV) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS XeThang (
            MaXeThang TEXT PRIMARY KEY,
            MaSV TEXT NOT NULL,
            BienSoXe TEXT NOT NULL,
            LoaiXe TEXT NOT NULL,
            NgayDangKy TEXT NOT NULL,
            GiaVeThang DECIMAL(12, 2) NOT NULL DEFAULT 100000.00,
            TrangThai INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (MaSV) REFERENCES SinhVien(MaSV) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS LuotGuiXe (
            MaLuot INTEGER PRIMARY KEY AUTOINCREMENT,
            MaXeThang TEXT NOT NULL,
            ThoiGianVao TEXT NOT NULL,
            ThoiGianRa TEXT,
            NgayGiaoDich TEXT NOT NULL,
            SoLieuLuotTrongNgay INTEGER NOT NULL DEFAULT 1,
            PhuPhiPhatSinh DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
            FOREIGN KEY (MaXeThang) REFERENCES XeThang(MaXeThang) ON DELETE CASCADE
        );

        -- Thêm dữ liệu mẫu ban đầu
        INSERT OR IGNORE INTO Phong VALUES ('P101', '101', 'Phòng 4 người (Điều hòa)', 1200000.00, 4);
        INSERT OR IGNORE INTO Phong VALUES ('P102', '102', 'Phòng 6 người (Quạt)', 800000.00, 6);
        INSERT OR IGNORE INTO Phong VALUES ('P201', '201', 'Phòng 2 người (VIP)', 2000000.00, 2);

        INSERT OR IGNORE INTO SinhVien VALUES ('SV001', '001202001111', 'Nguyễn Văn An', '2004-05-15', 'CNTT1-K17', 'Hà Nội', 'P101', '2024-09-01');
        INSERT OR IGNORE INTO SinhVien VALUES ('SV002', '001202002222', 'Trần Thị Bình', '2004-08-20', 'ATTT2-K17', 'Nam Định', 'P101', '2024-09-01');
        INSERT OR IGNORE INTO SinhVien VALUES ('SV003', '001202003333', 'Lê Hoàng Cường', '2005-02-10', 'DVT1-K18', 'Hải Phòng', 'P102', '2025-09-01');
        INSERT OR IGNORE INTO SinhVien VALUES ('SV004', '001202004444', 'Phạm Minh Đức', '2005-11-05', 'CNTT2-K18', 'Nghệ An', 'P201', '2025-09-01');

        INSERT OR IGNORE INTO KhachTham (SoCMT, HoTen, NgaySinh, MaSV, NgayDenChoi) VALUES ('001199005555', 'Nguyễn Văn Nam', '1980-01-01', 'SV001', '2026-10-05');
        INSERT OR IGNORE INTO KhachTham (SoCMT, HoTen, NgaySinh, MaSV, NgayDenChoi) VALUES ('001199006666', 'Trần Văn Hùng', '1978-04-12', 'SV002', '2026-10-10');

        INSERT OR IGNORE INTO DichVu VALUES ('DV01', 'Giặt là', 15000.00);
        INSERT OR IGNORE INTO DichVu VALUES ('DV02', 'Ăn sáng / Cơm ca', 30000.00);
        INSERT OR IGNORE INTO DichVu VALUES ('DV03', 'Cho thuê xe đạp', 20000.00);
        INSERT OR IGNORE INTO DichVu VALUES ('DV04', 'Rửa xe', 25000.00);

        INSERT OR IGNORE INTO SuDungDichVu (MaSV, MaDV, ThoiGianSuDung, SoLuong, ThanhTien) VALUES ('SV001', 'DV01', '2026-10-05 08:30:00', 3, 45000.00);
        INSERT OR IGNORE INTO SuDungDichVu (MaSV, MaDV, ThoiGianSuDung, SoLuong, ThanhTien) VALUES ('SV001', 'DV02', '2026-10-10 12:00:00', 5, 150000.00);
        INSERT OR IGNORE INTO SuDungDichVu (MaSV, MaDV, ThoiGianSuDung, SoLuong, ThanhTien) VALUES ('SV002', 'DV01', '2026-10-06 09:15:00', 2, 30000.00);
        INSERT OR IGNORE INTO SuDungDichVu (MaSV, MaDV, ThoiGianSuDung, SoLuong, ThanhTien) VALUES ('SV002', 'DV03', '2026-10-12 14:00:00', 1, 20000.00);
        INSERT OR IGNORE INTO SuDungDichVu (MaSV, MaDV, ThoiGianSuDung, SoLuong, ThanhTien) VALUES ('SV003', 'DV02', '2026-10-15 18:30:00', 10, 300000.00);
        INSERT OR IGNORE INTO SuDungDichVu (MaSV, MaDV, ThoiGianSuDung, SoLuong, ThanhTien) VALUES ('SV004', 'DV04', '2026-10-08 10:00:00', 2, 50000.00);

        INSERT OR IGNORE INTO XeThang VALUES ('XT01', 'SV001', '29-A1 123.45', 'Xe máy Wave', '2026-09-01', 100000.00, 1);
        INSERT OR IGNORE INTO XeThang VALUES ('XT02', 'SV001', '29-MD 888.88', 'Xe điện VinFast', '2026-09-15', 100000.00, 1);
        INSERT OR IGNORE INTO XeThang VALUES ('XT03', 'SV002', '18-B2 567.89', 'Xe máy Vision', '2026-09-01', 100000.00, 1);

        INSERT OR IGNORE INTO LuotGuiXe (MaXeThang, ThoiGianVao, ThoiGianRa, NgayGiaoDich, SoLieuLuotTrongNgay, PhuPhiPhatSinh) VALUES ('XT01', '2026-10-10 07:00:00', '2026-10-10 09:00:00', '2026-10-10', 1, 0.00);
        INSERT OR IGNORE INTO LuotGuiXe (MaXeThang, ThoiGianVao, ThoiGianRa, NgayGiaoDich, SoLieuLuotTrongNgay, PhuPhiPhatSinh) VALUES ('XT01', '2026-10-10 10:00:00', '2026-10-10 12:00:00', '2026-10-10', 2, 0.00);
        INSERT OR IGNORE INTO LuotGuiXe (MaXeThang, ThoiGianVao, ThoiGianRa, NgayGiaoDich, SoLieuLuotTrongNgay, PhuPhiPhatSinh) VALUES ('XT01', '2026-10-10 13:00:00', '2026-10-10 15:00:00', '2026-10-10', 3, 3000.00);
        INSERT OR IGNORE INTO LuotGuiXe (MaXeThang, ThoiGianVao, ThoiGianRa, NgayGiaoDich, SoLieuLuotTrongNgay, PhuPhiPhatSinh) VALUES ('XT01', '2026-10-10 17:00:00', '2026-10-10 21:00:00', '2026-10-10', 4, 3000.00);
        """)
        conn.commit()
    conn.close()

# TỰ ĐỘNG GỌI HÀM NÀY NGAY KHI APP ĐÓNG GÓI HOẶC PHÁT HÀNH CHẠY
init_db_if_not_exists()

# ----------------------------------------------------------------------------
# Kết nối & tiện ích Database
# ----------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def exec_sql(cur, sql, args=None):
    if args is not None:
        if isinstance(args, dict):
            for k in args:
                sql = sql.replace(f"%({k})s", f":{k}")
            cur.execute(sql, args)
        else:
            sql = sql.replace("%s", "?")
            cur.execute(sql, args)
    else:
        cur.execute(sql)


def query(sql, args=None, one=False):
    with get_db() as conn:
        cur = conn.cursor()
        exec_sql(cur, sql, args)
        if one:
            r = cur.fetchone()
            return dict(r) if r else None
        return [dict(r) for r in cur.fetchall()]


def db_message(e):
    msg = str(e)
    if "UNIQUE constraint failed" in msg:
        return "Dữ liệu bị trùng (mã hoặc số CMT đã tồn tại)."
    if "FOREIGN KEY constraint failed" in msg:
        return "Không thể xóa hoặc cập nhật vì dữ liệu đang được tham chiếu ở bảng khác."
    if "CHECK constraint failed" in msg:
        return "Giá trị không hợp lệ (vi phạm ràng buộc số phải >= 0 / > 0)."
    return msg


def today():
    return dt.date.today()


def month_range(thang, nam):
    first = dt.date(nam, thang, 1)
    nxt = dt.date(nam + (thang == 12), thang % 12 + 1, 1)
    return first, nxt - dt.timedelta(days=1)


def arg_int(name, default, lo, hi):
    try:
        v = int(request.args.get(name))
        return v if lo <= v <= hi else default
    except (TypeError, ValueError):
        return default


def arg_date(name, default):
    try:
        return dt.date.fromisoformat(request.args.get(name, ""))
    except ValueError:
        return default


def to_input(v):
    if v is None:
        return ""
    if isinstance(v, dt.datetime):
        return v.strftime("%Y-%m-%dT%H:%M")
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, Decimal):
        return f"{v:f}"
    return str(v)


def csv_response(filename, headers, rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for r in rows:
        out = []
        for v in r:
            if isinstance(v, Decimal):
                v = int(v) if v == v.to_integral() else float(v)
            out.append(v)
        w.writerow(out)
    return Response(
        "\ufeff" + buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ----------------------------------------------------------------------------
# Bộ lọc Jinja
# ----------------------------------------------------------------------------
@app.template_filter("vnd")
def vnd(v):
    if v is None:
        return "0 đ"
    return f"{int(round(v)):,}".replace(",", ".") + " đ"


@app.template_filter("fmt")
def fmt(v, kind="text"):
    if kind == "bool":
        return Markup('<span class="badge bg-success">Hiệu lực</span>') if v else Markup('<span class="badge bg-secondary">Đã hủy</span>')
    if v is None or v == "":
        return Markup('<span class="text-muted">—</span>')
    if kind == "money":
        return vnd(v)
    if kind == "datetime" and isinstance(v, dt.datetime):
        return v.strftime("%d/%m/%Y %H:%M")
    if kind in ("date", "datetime") and isinstance(v, dt.date):
        return v.strftime("%d/%m/%Y")
    return escape(v)


@app.template_filter("dmy")
def dmy(v):
    return v.strftime("%d/%m/%Y") if v else ""


NAV = [
    ("Tổng quan", [("/", "Bảng điều khiển")]),
    ("Quản lý", [
        ("/sinh-vien", "Sinh viên"),
        ("/phong", "Phòng ở"),
        ("/khach", "Khách đến thăm"),
        ("/dich-vu", "Danh mục dịch vụ"),
        ("/su-dung-dv", "Sử dụng dịch vụ"),
        ("/xe-thang", "Xe vé tháng"),
        ("/luot-gui-xe", "Lượt gửi/lấy xe"),
    ]),
    ("Báo cáo & truy vấn", [
        ("/bao-cao/hoa-don", "1. Hóa đơn hàng tháng"),
        ("/bao-cao/dich-vu-sv", "2. Dịch vụ theo khoảng ngày"),
        ("/bao-cao/khach", "3. Khách thăm (tuần/tháng)"),
        ("/bao-cao/doanh-thu", "4. Doanh thu dịch vụ"),
    ]),
]


@app.context_processor
def inject_nav():
    return dict(NAV=NAV, now_year=today().year)


# ----------------------------------------------------------------------------
# CRUD tổng quát cho các bảng
# ----------------------------------------------------------------------------
def F(name, label, type="text", required=True, **kw):
    return dict(name=name, label=label, type=type, required=required, **kw)


def C(key, label, kind="text"):
    return dict(key=key, label=label, kind=kind)


OPT_SV = "SELECT MaSV AS v, MaSV || ' - ' || HoTen AS l FROM SinhVien ORDER BY MaSV"
OPT_PHONG = ("SELECT MaPhong AS v, 'Phòng ' || SoPhong || ' - ' || LoaiPhong || ' (tối đa ' || SoNguoiToiDa || ' người)' AS l "
             "FROM Phong ORDER BY SoPhong")
OPT_DV = "SELECT MaDV AS v, TenDV || ' - ' || DonGia || 'đ' AS l FROM DichVu ORDER BY MaDV"
OPT_XE = ("SELECT x.MaXeThang AS v, x.MaXeThang || ' - ' || x.BienSoXe || ' (' || sv.HoTen || ')' AS l "
          "FROM XeThang x JOIN SinhVien sv ON sv.MaSV = x.MaSV ORDER BY x.MaXeThang")
OPT_TRANGTHAI = [dict(v="1", l="Đang hiệu lực"), dict(v="0", l="Đã hủy")]


def to_int(v, label):
    try:
        return int(v)
    except (TypeError, ValueError):
        raise ValueError(f"{label} phải là số nguyên.")


def v_sinhvien(vals, old, cur):
    mp = vals.get("MaPhong")
    if mp and (old is None or old.get("MaPhong") != mp):
        exec_sql(cur, "SELECT SoNguoiToiDa FROM Phong WHERE MaPhong=%s", (mp,))
        p = cur.fetchone()
        exec_sql(cur, "SELECT COUNT(*) AS n FROM SinhVien WHERE MaPhong=%s", (mp,))
        n = cur.fetchone()["n"]
        if p and n >= p["SoNguoiToiDa"]:
            raise ValueError("Lỗi: Phòng đã đạt số lượng người ở tối đa!")


def v_xe(vals, old, cur):
    vals["TrangThai"] = to_int(vals["TrangThai"], "Trạng thái")
    changed = old is None or not old["TrangThai"] or old["MaSV"] != vals["MaSV"]
    if vals["TrangThai"] == 1 and changed:
        exec_sql(cur, "SELECT COUNT(*) AS n FROM XeThang WHERE MaSV=%s AND TrangThai=1", (vals["MaSV"],))
        if cur.fetchone()["n"] >= 2:
            raise ValueError("Lỗi: Mỗi sinh viên chỉ được đăng ký tối đa 2 xe vé tháng!")


def v_sudung(vals, old, cur):
    sl = to_int(vals["SoLuong"], "Số lượng")
    if sl <= 0:
        raise ValueError("Số lượng phải lớn hơn 0.")
    exec_sql(cur, "SELECT DonGia FROM DichVu WHERE MaDV=%s", (vals["MaDV"],))
    dv = cur.fetchone()
    if not dv:
        raise ValueError("Dịch vụ không tồn tại.")
    vals["SoLuong"] = sl
    vals["ThanhTien"] = dv["DonGia"] * sl


def v_luot(vals, old, cur):
    vao, ra = vals["ThoiGianVao"], vals.get("ThoiGianRa")
    if ra and ra < vao:
        raise ValueError("Thời gian lấy xe phải sau thời gian gửi xe.")
    vals["NgayGiaoDich"] = vao[:10]
    if old is None:
        vals["SoLieuLuotTrongNgay"] = 1
        vals["PhuPhiPhatSinh"] = 0


def recompute_luot(cur, xe, ngay):
    exec_sql(cur, "SELECT MaLuot FROM LuotGuiXe WHERE MaXeThang=%s AND NgayGiaoDich=%s "
                  "ORDER BY ThoiGianVao, MaLuot", (xe, ngay))
    for i, r in enumerate(cur.fetchall(), 1):
        exec_sql(cur, "UPDATE LuotGuiXe SET SoLieuLuotTrongNgay=%s, PhuPhiPhatSinh=%s WHERE MaLuot=%s",
                      (i, 3000 if i > 2 else 0, r["MaLuot"]))


def after_save_luot(cur, old, vals):
    recompute_luot(cur, vals["MaXeThang"], vals["NgayGiaoDich"])
    if old and (str(old["MaXeThang"]) != str(vals["MaXeThang"]) or str(old["NgayGiaoDich"]) != str(vals["NgayGiaoDich"])):
        recompute_luot(cur, old["MaXeThang"], old["NgayGiaoDich"])


def after_delete_luot(cur, old):
    recompute_luot(cur, old["MaXeThang"], old["NgayGiaoDich"])


ENT = {
    "sinh-vien": dict(
        table="SinhVien", pk="MaSV", title="Sinh viên", desc="Danh sách sinh viên đang ở / đăng ký ở KTX.",
        sql=("SELECT sv.*, p.SoPhong FROM SinhVien sv LEFT JOIN Phong p ON p.MaPhong = sv.MaPhong "
             "{where} ORDER BY sv.MaSV"),
        search=["sv.MaSV", "sv.HoTen", "sv.Lop", "sv.QueQuan", "sv.SoCMT"],
        columns=[C("MaSV", "Mã SV"), C("HoTen", "Họ tên"), C("SoCMT", "Số CMT"), C("NgaySinh", "Ngày sinh", "date"),
                 C("Lop", "Lớp"), C("QueQuan", "Quê quán"), C("SoPhong", "Phòng"), C("NgayBatDauO", "Bắt đầu ở", "date")],
        fields=[F("MaSV", "Mã sinh viên", pk=True), F("SoCMT", "Số CMT/CCCD"), F("HoTen", "Họ và tên"),
                F("NgaySinh", "Ngày sinh", "date"), F("Lop", "Lớp"), F("QueQuan", "Quê quán"),
                F("MaPhong", "Phòng ở", "select", False, options=OPT_PHONG),
                F("NgayBatDauO", "Ngày bắt đầu ở", "date", False, default=today)],
        validate=v_sinhvien,
        delete_warn="Xóa sinh viên sẽ xóa luôn khách thăm, lịch sử dịch vụ và xe vé tháng của sinh viên này. Tiếp tục?",
    ),
    "phong": dict(
        table="Phong", pk="MaPhong", title="Phòng ở", desc="Danh mục phòng, đơn giá (tính chẵn tháng) và sức chứa.",
        sql=("SELECT p.*, COUNT(sv.MaSV) AS DangO, p.SoNguoiToiDa - COUNT(sv.MaSV) AS ConTrong "
             "FROM Phong p LEFT JOIN SinhVien sv ON sv.MaPhong = p.MaPhong GROUP BY p.MaPhong ORDER BY p.SoPhong"),
        columns=[C("MaPhong", "Mã phòng"), C("SoPhong", "Số phòng"), C("LoaiPhong", "Loại phòng"),
                 C("DonGia", "Đơn giá/tháng", "money"), C("SoNguoiToiDa", "Tối đa"), C("DangO", "Dang ở"),
                 C("ConTrong", "Còn trống")],
        fields=[F("MaPhong", "Mã phòng", pk=True), F("SoPhong", "Số phòng"), F("LoaiPhong", "Loại phòng"),
                F("DonGia", "Đơn giá / tháng (VNĐ)", "number"), F("SoNguoiToiDa", "Số người tối đa", "number")],
        delete_warn="Xóa phòng? Sinh viên đang ở phòng này sẽ chuyển sang trạng thái 'Chưa xếp phòng'.",
    ),
    "khach": dict(
        table="KhachTham", pk="MaKhach", auto=True, title="Khách đến thăm",
        desc="Mỗi lần khách đến chơi được ghi 1 dòng (CMT, tên, ngày sinh, sinh viên được thăm, ngày đến).",
        sql=("SELECT k.*, sv.HoTen AS TenSV FROM KhachTham k JOIN SinhVien sv ON sv.MaSV = k.MaSV "
             "{where} ORDER BY k.NgayDenChoi DESC, k.MaKhach DESC"),
        search=["k.HoTen", "k.SoCMT", "sv.HoTen", "sv.MaSV"],
        columns=[C("NgayDenChoi", "Ngày đến", "date"), C("SoCMT", "CMT khách"), C("HoTen", "Tên khách"),
                 C("NgaySinh", "Ngày sinh", "date"), C("MaSV", "Mã SV"), C("TenSV", "Sinh viên được thăm")],
        fields=[F("SoCMT", "Số CMT/CCCD của khách"), F("HoTen", "Họ tên khách"), F("NgaySinh", "Ngày sinh", "date", False),
                F("MaSV", "Sinh viên được thăm", "select", options=OPT_SV),
                F("NgayDenChoi", "Ngày đến chơi", "date", default=today)],
    ),
    "dich-vu": dict(
        table="DichVu", pk="MaDV", title="Danh mục dịch vụ", desc="Giặt là, ăn uống, cho thuê xe, rửa xe…",
        sql="SELECT * FROM DichVu {where} ORDER BY MaDV",
        columns=[C("MaDV", "Mã DV"), C("TenDV", "Tên dịch vụ"), C("DonGia", "Đơn giá", "money")],
        fields=[F("MaDV", "Mã dịch vụ", pk=True), F("TenDV", "Tên dịch vụ"), F("DonGia", "Đơn giá (VNĐ)", "number")],
        delete_warn="Xóa dịch vụ sẽ xóa luôn toàn bộ lịch sử sử dụng dịch vụ này. Tiếp tục?",
    ),
    "su-dung-dv": dict(
        table="SuDungDichVu", pk="MaSDDV", auto=True, title="Sử dụng dịch vụ",
        desc="Nhật ký sinh viên dùng dịch vụ. Thành tiền = đơn giá × số lượng.",
        sql=("SELECT s.*, sv.HoTen, d.TenDV FROM SuDungDichVu s JOIN SinhVien sv ON sv.MaSV = s.MaSV "
             "JOIN DichVu d ON d.MaDV = s.MaDV {where} ORDER BY s.ThoiGianSuDung DESC, s.MaSDDV DESC"),
        search=["sv.HoTen", "s.MaSV", "d.TenDV"],
        columns=[C("ThoiGianSuDung", "Thời gian", "datetime"), C("MaSV", "Mã SV"), C("HoTen", "Sinh viên"),
                 C("TenDV", "Dịch vụ"), C("SoLuong", "Số lượng"), C("ThanhTien", "Thành tiền", "money")],
        fields=[F("MaSV", "Sinh viên", "select", options=OPT_SV), F("MaDV", "Dịch vụ", "select", options=OPT_DV),
                F("ThoiGianSuDung", "Thời gian sử dụng", "datetime",
                  default=lambda: dt.datetime.now().replace(second=0, microsecond=0)),
                F("SoLuong", "Số lượng / số lần", "number", default="1")],
        validate=v_sudung,
    ),
    "xe-thang": dict(
        table="XeThang", pk="MaXeThang", title="Xe vé tháng",
        desc="Vé gửi xe tháng (100.000đ/tháng). Mỗi sinh viên tối đa 2 xe đang hiệu lực.",
        sql=("SELECT x.*, sv.HoTen FROM XeThang x JOIN SinhVien sv ON sv.MaSV = x.MaSV "
             "{where} ORDER BY x.MaXeThang"),
        search=["x.BienSoXe", "sv.HoTen", "x.MaSV", "x.MaXeThang"],
        columns=[C("MaXeThang", "Mã vé"), C("BienSoXe", "Biển số"), C("LoaiXe", "Loại xe"), C("MaSV", "Mã SV"),
                 C("HoTen", "Chủ xe"), C("NgayDangKy", "Ngày đăng ký", "date"),
                 C("GiaVeThang", "Giá vé tháng", "money"), C("TrangThai", "Trạng thái", "bool")],
        fields=[F("MaXeThang", "Mã vé xe tháng", pk=True), F("MaSV", "Sinh viên (chủ xe)", "select", options=OPT_SV),
                F("BienSoXe", "Biển số xe"), F("LoaiXe", "Loại xe"),
                F("NgayDangKy", "Ngày đăng ký", "date", default=today),
                F("GiaVeThang", "Giá vé tháng (VNĐ)", "number", default="100000"),
                F("TrangThai", "Trạng thái", "select", options=OPT_TRANGTHAI, default="1", no_blank=True)],
        validate=v_xe,
    ),
    "luot-gui-xe": dict(
        table="LuotGuiXe", pk="MaLuot", auto=True, title="Lượt gửi/lấy xe vé tháng",
        desc="Mỗi xe được 2 lượt miễn phí/ngày; từ lượt thứ 3 phụ phí 3.000đ/lượt.",
        sql=("SELECT l.*, x.BienSoXe, sv.HoTen FROM LuotGuiXe l JOIN XeThang x ON x.MaXeThang = l.MaXeThang "
             "JOIN SinhVien sv ON sv.MaSV = x.MaSV {where} ORDER BY l.ThoiGianVao DESC, l.MaLuot DESC"),
        search=["x.BienSoXe", "sv.HoTen", "l.MaXeThang"],
        columns=[C("NgayGiaoDich", "Ngày", "date"), C("MaXeThang", "Mã vé"), C("BienSoXe", "Biển số"),
                 C("HoTen", "Chủ xe"), C("ThoiGianVao", "Gửi xe lúc", "datetime"),
                 C("ThoiGianRa", "Lấy xe lúc", "datetime"), C("SoLieuLuotTrongNgay", "Lượt thứ"),
                 C("PhuPhiPhatSinh", "Phụ phí", "money")],
        fields=[F("MaXeThang", "Xe vé tháng", "select", options=OPT_XE),
                F("ThoiGianVao", "Thời gian gửi xe", "datetime",
                  default=lambda: dt.datetime.now().replace(second=0, microsecond=0)),
                F("ThoiGianRa", "Thời gian lấy xe", "datetime", False)],
        validate=v_luot, after_save=after_save_luot, after_delete=after_delete_luot,
    ),
}


def collect(cfg, form, editing):
    vals = {}
    for f in cfg["fields"]:
        if f.get("pk") and editing:
            continue
        v = form.get(f["name"], "").strip()
        if v == "":
            if f["required"]:
                raise ValueError(f"Vui lòng nhập: {f['label']}.")
            vals[f["name"]] = None
            continue
        if f["type"] == "datetime":
            v = v.replace("T", " ")
            if len(v) == 16:
                v += ":00"
        elif f["type"] == "number":
            try:
                Decimal(v)
            except Exception:
                raise ValueError(f"{f['label']} phải là số.")
        vals[f["name"]] = v
    return vals


def do_save(cfg, form, pk=None):
    db = get_db()
    with db:
        cur = db.cursor()
        old = None
        if pk is not None:
            exec_sql(cur, f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']}=%s", (pk,))
            old = cur.fetchone()
            if old is None:
                abort(404)
        vals = collect(cfg, form, editing=pk is not None)
        if cfg.get("validate"):
            cfg["validate"](vals, old, cur)
        cols = list(vals)
        if pk is None:
            placeholders = ", ".join(["?"] * len(cols))
            exec_sql(cur, f"INSERT INTO {cfg['table']} ({', '.join(cols)}) VALUES ({placeholders})", list(vals.values()))
        else:
            set_clause = ", ".join(c + "=?" for c in cols)
            exec_sql(cur, f"UPDATE {cfg['table']} SET {set_clause} WHERE {cfg['pk']}=%s", list(vals.values()) + [pk])
        if cfg.get("after_save"):
            cfg["after_save"](cur, old, vals)


def list_view(key):
    cfg = ENT[key]
    q = request.args.get("q", "").strip()
    where, args = "", None
    if q and cfg.get("search"):
        where = "WHERE " + " OR ".join(f"{c} LIKE %s" for c in cfg["search"])
        args = [f"%{q}%"] * len(cfg["search"])
    rows = query(cfg["sql"].replace("{where}", where), args)
    return render_template("list.html", key=key, cfg=cfg, rows=rows, q=q)


def form_view(key, pk=None):
    cfg = ENT[key]
    editing = pk is not None
    row = None
    if editing:
        row = query(f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']}=%s", (pk,), one=True)
        if row is None:
            abort(404)
    values = {}
    if request.method == "POST":
        try:
            do_save(cfg, request.form, pk)
            flash("Đã lưu thành công.", "success")
            return redirect(f"/{key}")
        except ValueError as e:
            flash(str(e), "danger")
        except sqlite3.Error as e:
            flash(db_message(e), "danger")
        values = request.form.to_dict()
    else:
        for f in cfg["fields"]:
            if row is not None:
                values[f["name"]] = to_input(row.get(f["name"]))
            else:
                d = f.get("default")
                values[f["name"]] = to_input(d() if callable(d) else d)
    options = {}
    for f in cfg["fields"]:
        if f["type"] == "select":
            o = f["options"]
            options[f["name"]] = query(o) if isinstance(o, str) else o
    return render_template("form.html", key=key, cfg=cfg, values=values, options=options, editing=editing, pk=pk)


def delete_view(key, pk):
    cfg = ENT[key]
    db = get_db()
    try:
        with db:
            cur = db.cursor()
            exec_sql(cur, f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']}=%s", (pk,))
            old = cur.fetchone()
            if old is None:
                abort(404)
            exec_sql(cur, f"DELETE FROM {cfg['table']} WHERE {cfg['pk']}=%s", (pk,))
            if cfg.get("after_delete"):
                cfg["after_delete"](cur, old)
        flash("Đã xóa.", "success")
    except sqlite3.Error as e:
        flash(db_message(e), "danger")
    return redirect(f"/{key}")


for _key in ENT:
    app.add_url_rule(f"/{_key}", f"{_key}_list", list_view, defaults={"key": _key})
    app.add_url_rule(f"/{_key}/new", f"{_key}_new", form_view, defaults={"key": _key}, methods=["GET", "POST"])
    app.add_url_rule(f"/{_key}/<pk>/edit", f"{_key}_edit", form_view, defaults={"key": _key}, methods=["GET", "POST"])
    app.add_url_rule(f"/{_key}/<pk>/delete", f"{_key}_delete", delete_view, defaults={"key": _key}, methods=["POST"])


# ----------------------------------------------------------------------------
# Báo cáo 1: Hóa đơn hàng tháng
# ----------------------------------------------------------------------------
BILL_SQL = """
SELECT sv.MaSV, sv.HoTen, sv.Lop, sv.QueQuan, sv.NgayBatDauO,
       COALESCE(p.SoPhong, 'Chưa xếp') AS SoPhong,
       CASE WHEN p.MaPhong IS NOT NULL AND (sv.NgayBatDauO IS NULL OR sv.NgayBatDauO <= :last)
            THEN p.DonGia ELSE 0 END AS TienPhong,
       COALESCE(dv.Tong, 0) AS TienDichVu,
       COALESCE(xe.Tong, 0) AS TienVeXe,
       COALESCE(pp.Tong, 0) AS PhuPhiXe
FROM SinhVien sv
LEFT JOIN Phong p ON p.MaPhong = sv.MaPhong
LEFT JOIN (SELECT MaSV, SUM(ThanhTien) AS Tong FROM SuDungDichVu
           WHERE ThoiGianSuDung >= :first AND ThoiGianSuDung < date(:last, '+1 day')
           GROUP BY MaSV) dv ON dv.MaSV = sv.MaSV
LEFT JOIN (SELECT MaSV, SUM(GiaVeThang) AS Tong FROM XeThang
           WHERE TrangThai = 1 AND NgayDangKy <= :last GROUP BY MaSV) xe ON xe.MaSV = sv.MaSV
LEFT JOIN (SELECT x.MaSV, SUM(l.PhuPhiPhatSinh) AS Tong FROM LuotGuiXe l
           JOIN XeThang x ON x.MaXeThang = l.MaXeThang
           WHERE l.NgayGiaoDich BETWEEN :first AND :last GROUP BY x.MaSV) pp ON pp.MaSV = sv.MaSV
{where}
ORDER BY sv.MaSV
"""


def bill_rows(thang, nam, masv=None, q=None):
    first, last = month_range(thang, nam)
    params = dict(first=first.isoformat(), last=last.isoformat())
    where = ""
    if masv:
        where, params["masv"] = "WHERE sv.MaSV = :masv", masv
    elif q:
        where = "WHERE (sv.MaSV LIKE :q OR sv.HoTen LIKE :q OR sv.Lop LIKE :q)"
        params["q"] = f"%{q}%"
    rows = query(BILL_SQL.replace("{where}", where), params)
    for r in rows:
        r["TongCong"] = r["TienPhong"] + r["TienDichVu"] + r["TienVeXe"] + r["PhuPhiXe"]
    return rows


@app.route("/bao-cao/hoa-don")
def rp_hoadon():
    t = today()
    thang, nam = arg_int("thang", t.month, 1, 12), arg_int("nam", t.year, 2000, 2100)
    q = request.args.get("q", "").strip()
    rows = bill_rows(thang, nam, q=q)
    if request.args.get("csv"):
        return csv_response(f"hoa-don-{nam}-{thang:02d}.csv",
                            ["Mã SV", "Họ tên", "Lớp", "Phòng", "Tiền phòng", "Dịch vụ", "Vé xe tháng", "Phụ phí gửi xe", "Tổng cộng"],
                            [[r["MaSV"], r["HoTen"], r["Lop"], r["SoPhong"], r["TienPhong"], r["TienDichVu"],
                              r["TienVeXe"], r["PhuPhiXe"], r["TongCong"]] for r in rows])
    tot = {k: sum(r[k] for r in rows) for k in ("TienPhong", "TienDichVu", "TienVeXe", "PhuPhiXe", "TongCong")}
    return render_template("bc_hoadon.html", rows=rows, tot=tot, thang=thang, nam=nam, q=q)


@app.route("/hoa-don/<masv>")
def hoadon(masv):
    t = today()
    thang, nam = arg_int("thang", t.month, 1, 12), arg_int("nam", t.year, 2000, 2100)
    rows = bill_rows(thang, nam, masv=masv)
    if not rows:
        abort(404)
    first, last = month_range(thang, nam)
    dv = query("SELECT s.ThoiGianSuDung, d.TenDV, d.DonGia, s.SoLuong, s.ThanhTien FROM SuDungDichVu s "
               "JOIN DichVu d ON d.MaDV = s.MaDV WHERE s.MaSV = ? AND s.ThoiGianSuDung >= ? "
               "AND s.ThoiGianSuDung < date(?, '+1 day') ORDER BY s.ThoiGianSuDung",
               (masv, first.isoformat(), last.isoformat()))
    xe = query("SELECT MaXeThang, BienSoXe, LoaiXe, GiaVeThang FROM XeThang WHERE MaSV = ? AND TrangThai = 1 "
               "AND NgayDangKy <= ? ORDER BY MaXeThang", (masv, last.isoformat()))
    pp = query("SELECT l.NgayGiaoDich, x.BienSoXe, COUNT(*) AS SoLuot, SUM(l.PhuPhiPhatSinh) AS PhuPhi "
               "FROM LuotGuiXe l JOIN XeThang x ON x.MaXeThang = l.MaXeThang "
               "WHERE x.MaSV = ? AND l.NgayGiaoDich BETWEEN ? AND ? "
               "GROUP BY l.NgayGiaoDich, x.BienSoXe HAVING SUM(l.PhuPhiPhatSinh) > 0 ORDER BY l.NgayGiaoDich",
               (masv, first.isoformat(), last.isoformat()))
    phong = query("SELECT p.* FROM Phong p JOIN SinhVien sv ON sv.MaPhong = p.MaPhong WHERE sv.MaSV = ?", (masv,), one=True)
    return render_template("hoadon.html", b=rows[0], dv=dv, xe=xe, pp=pp, phong=phong, thang=thang, nam=nam)


# ----------------------------------------------------------------------------
# Báo cáo 2: Dịch vụ của sinh viên
# ----------------------------------------------------------------------------
@app.route("/bao-cao/dich-vu-sv")
def rp_dichvu():
    t = today()
    tu, den = arg_date("tu", t.replace(day=1)), arg_date("den", t)
    masv = request.args.get("masv", "").strip()
    sql = ("SELECT sv.MaSV, sv.HoTen, sv.Lop, sv.QueQuan, d.MaDV, d.TenDV, d.DonGia, "
           "SUM(s.SoLuong) AS TongSoLuong, SUM(s.ThanhTien) AS TongTien "
           "FROM SuDungDichVu s JOIN SinhVien sv ON sv.MaSV = s.MaSV JOIN DichVu d ON d.MaDV = s.MaDV "
           "WHERE s.ThoiGianSuDung >= ? AND s.ThoiGianSuDung < date(?, '+1 day') ")
    args = [tu.isoformat(), den.isoformat()]
    if masv:
        sql += "AND sv.MaSV = ? "
        args.append(masv)
    sql += ("GROUP BY sv.MaSV, sv.HoTen, sv.Lop, sv.QueQuan, d.MaDV, d.TenDV, d.DonGia "
            "ORDER BY sv.MaSV, d.MaDV")
    rows = query(sql, args)
    if request.args.get("csv"):
        return csv_response(f"dich-vu-{tu}-{den}.csv",
                            ["Mã SV", "Họ tên", "Lớp", "Quê quán", "Dịch vụ", "Đơn giá", "Tổng số lượng", "Tổng tiền"],
                            [[r["MaSV"], r["HoTen"], r["Lop"], r["QueQuan"], r["TenDV"], r["DonGia"],
                              r["TongSoLuong"], r["TongTien"]] for r in rows])
    total = sum(r["TongTien"] for r in rows)
    return render_template("bc_dichvu.html", rows=rows, tu=tu, den=den, masv=masv, total=total, svs=query(OPT_SV))


# ----------------------------------------------------------------------------
# Báo cáo 3: Khách đến thăm sinh viên
# ----------------------------------------------------------------------------
@app.route("/bao-cao/khach")
def rp_khach():
    kieu = request.args.get("kieu", "thang")
    if kieu not in ("tuan", "thang"):
        kieu = "thang"
    ngay = arg_date("ngay", today())
    if kieu == "tuan":
        first = ngay - dt.timedelta(days=ngay.weekday())
        last = first + dt.timedelta(days=6)
    else:
        first, last = month_range(ngay.month, ngay.year)
    rows = query(
        "SELECT sv.MaSV, sv.HoTen AS TenSV, sv.Lop, p.SoPhong, k.SoCMT, k.HoTen AS TenKhach, k.NgaySinh, "
        "COUNT(*) AS SoLan, "
        "group_concat(substr(k.NgayDenChoi, 9, 2) || '/' || substr(k.NgayDenChoi, 6, 2), ', ') AS CacNgay "
        "FROM KhachTham k JOIN SinhVien sv ON sv.MaSV = k.MaSV LEFT JOIN Phong p ON p.MaPhong = sv.MaPhong "
        "WHERE k.NgayDenChoi BETWEEN ? AND ? "
        "GROUP BY sv.MaSV, sv.HoTen, sv.Lop, p.SoPhong, k.SoCMT, k.HoTen, k.NgaySinh "
        "ORDER BY sv.MaSV, k.HoTen", (first.isoformat(), last.isoformat()))
    if request.args.get("csv"):
        return csv_response(f"khach-tham-{first}-{last}.csv",
                            ["Mã SV", "Sinh viên", "Lớp", "Phòng", "CMT khách", "Tên khách", "Ngày sinh khách", "Số lần đến", "Các ngày đến"],
                            [[r["MaSV"], r["TenSV"], r["Lop"], r["SoPhong"], r["SoCMT"], r["TenKhach"], r["NgaySinh"],
                              r["SoLan"], r["CacNgay"]] for r in rows])
    return render_template("bc_khach.html", rows=rows, kieu=kieu, ngay=ngay, first=first, last=last,
                           tong_lan=sum(r["SoLan"] for r in rows))


# ----------------------------------------------------------------------------
# Báo cáo 4: Doanh thu từng dịch vụ theo tháng
# ----------------------------------------------------------------------------
@app.route("/bao-cao/doanh-thu")
def rp_doanhthu():
    nam = arg_int("nam", today().year, 2000, 2100)
    rows = query(
        "SELECT d.MaDV, d.TenDV, CAST(strftime('%m', s.ThoiGianSuDung) AS INTEGER) AS Thang, SUM(s.ThanhTien) AS DoanhThu "
        "FROM DichVu d LEFT JOIN SuDungDichVu s ON s.MaDV = d.MaDV AND CAST(strftime('%Y', s.ThoiGianSuDung) AS INTEGER) = ? "
        "GROUP BY d.MaDV, d.TenDV, CAST(strftime('%m', s.ThoiGianSuDung) AS INTEGER) ORDER BY d.MaDV", (nam,))
    dvs = {}
    for r in rows:
        d = dvs.setdefault(r["MaDV"], dict(MaDV=r["MaDV"], TenDV=r["TenDV"], thang=[Decimal(0)] * 12))
        if r["Thang"]:
            d["thang"][r["Thang"] - 1] += r["DoanhThu"] or 0
    table = list(dvs.values())
    for d in table:
        d["tong"] = sum(d["thang"])
    col_tot = [sum(d["thang"][i] for d in table) for i in range(12)]
    grand = sum(col_tot)
    if request.args.get("csv"):
        return csv_response(f"doanh-thu-dich-vu-{nam}.csv",
                            ["Mã DV", "Tên dịch vụ"] + [f"Tháng {i}" for i in range(1, 13)] + ["Cả năm"],
                            [[d["MaDV"], d["TenDV"]] + d["thang"] + [d["tong"]] for d in table]
                            + [["", "TỔNG"] + col_tot + [grand]])
    chart = dict(labels=[f"T{i}" for i in range(1, 13)],
                 sets=[dict(label=d["TenDV"], data=[float(x) for x in d["thang"]]) for d in table])
    return render_template("bc_doanhthu.html", table=table, col_tot=col_tot, grand=grand, nam=nam, chart=chart)


# ----------------------------------------------------------------------------
# Bảng điều khiển (Dashboard)
# ----------------------------------------------------------------------------
@app.route("/")
def index():
    t = today()
    first, last = month_range(t.month, t.year)
    st = query(
        "SELECT (SELECT COUNT(*) FROM SinhVien) AS sv, "
        "(SELECT COUNT(*) FROM Phong) AS phong, "
        "(SELECT COALESCE(SUM(SoNguoiToiDa), 0) FROM Phong) AS suc_chua, "
        "(SELECT COUNT(*) FROM SinhVien WHERE MaPhong IS NOT NULL) AS dang_o, "
        "(SELECT COUNT(*) FROM KhachTham WHERE NgayDenChoi BETWEEN ? AND ?) AS khach, "
        "(SELECT COUNT(*) FROM XeThang WHERE TrangThai = 1) AS xe", (first.isoformat(), last.isoformat()), one=True)
    bills = bill_rows(t.month, t.year)
    tong_thu = sum(b["TongCong"] for b in bills)
    rooms = query("SELECT p.SoPhong, p.LoaiPhong, p.SoNguoiToiDa, COUNT(sv.MaSV) AS DangO FROM Phong p "
                  "LEFT JOIN SinhVien sv ON sv.MaPhong = p.MaPhong "
                  "GROUP BY p.MaPhong, p.SoPhong, p.LoaiPhong, p.SoNguoiToiDa ORDER BY p.SoPhong")
    dvs = query("SELECT d.TenDV, COALESCE(SUM(s.ThanhTien), 0) AS DoanhThu, COALESCE(SUM(s.SoLuong), 0) AS SoLuot "
                "FROM DichVu d LEFT JOIN SuDungDichVu s ON s.MaDV = d.MaDV AND s.ThoiGianSuDung >= ? "
                "AND s.ThoiGianSuDung < date(?, '+1 day') GROUP BY d.MaDV, d.TenDV ORDER BY DoanhThu DESC",
                (first.isoformat(), last.isoformat()))
    return render_template("index.html", st=st, tong_thu=tong_thu, rooms=rooms, dvs=dvs, thang=t.month, nam=t.year)


@app.errorhandler(sqlite3.Error)
def handle_db_error(e):
    return render_template("error.html", msg=db_message(e)), 500


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", msg="Không tìm thấy trang hoặc bản ghi yêu cầu."), 404


# ----------------------------------------------------------------------------
# Luồng khởi chạy Flask ngầm & Khởi tạo PyWebView (Desktop Application)
# ----------------------------------------------------------------------------
def run_flask():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    init_db_if_not_exists()

    # Chạy Flask Server ở luồng ngầm (Background Thread)
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Mở cửa sổ ứng dụng Desktop thông qua pywebview
    webview.create_window(
        title="Hệ Thống Quản Lý Ký Túc Xá Sinh Viên",
        url="http://127.0.0.1:5000",
        width=1280,
        height=800,
        min_size=(1024, 600)
    )
    webview.start()