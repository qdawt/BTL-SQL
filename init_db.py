# -*- coding: utf-8 -*-
"""Khởi tạo CSDL MySQL từ file database/KTXSV.sql (tạo bảng, trigger, dữ liệu mẫu).

Cách dùng:
    python init_db.py            # tạo CSDL nếu chưa có
    python init_db.py --reset    # XÓA và tạo lại toàn bộ CSDL

Cấu hình kết nối qua biến môi trường: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME.
"""
import os
import sys

import pymysql

SQL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "KTXSV.sql")

HOST = os.environ.get("DB_HOST", "localhost")
PORT = int(os.environ.get("DB_PORT", "3306"))
USER = os.environ.get("DB_USER", "root")
PASSWORD = os.environ.get("DB_PASSWORD", "")
NAME = os.environ.get("DB_NAME", "ktx")


def strip_comment(line):
    """Bỏ phần chú thích '-- ...' ở cuối dòng (không cắt nhầm trong chuỗi '...')."""
    out, quote, i = [], None, 0
    while i < len(line):
        c = line[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < len(line):
                out.append(line[i + 1])
                i += 1
            elif c == quote:
                quote = None
        elif c in ("'", '"'):
            quote = c
            out.append(c)
        elif line.startswith("--", i):
            break
        else:
            out.append(c)
        i += 1
    return "".join(out).rstrip()


def split_statements(text):
    """Tách file .sql thành từng câu lệnh, hiểu lệnh DELIMITER của MySQL (dùng cho trigger)."""
    delim, buf, stmts = ";", [], []
    for raw in text.splitlines():
        line = strip_comment(raw)
        if not line.strip():
            continue
        if line.strip().upper().startswith("DELIMITER "):
            delim = line.strip().split(None, 1)[1]
            continue
        buf.append(line)
        if line.rstrip().endswith(delim):
            stmt = "\n".join(buf).rstrip()
            stmt = stmt[: -len(delim)].strip()
            buf = []
            if stmt:
                stmts.append(stmt)
    return stmts


def main():
    reset = "--reset" in sys.argv
    with open(SQL_FILE, encoding="utf-8") as f:
        stmts = split_statements(f.read())

    conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, charset="utf8mb4")
    try:
        with conn.cursor() as cur:
            if reset:
                cur.execute(f"DROP DATABASE IF EXISTS `{NAME}`")
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.execute(f"USE `{NAME}`")
            cur.execute("SHOW TABLES LIKE 'Phong'")
            if cur.fetchone():
                print(f"CSDL '{NAME}' đã được khởi tạo trước đó. Dùng 'python init_db.py --reset' để tạo lại.")
                return
            n = 0
            for s in stmts:
                if s.lstrip().upper().startswith("SELECT"):
                    continue  # các truy vấn mẫu trong file .sql đã được cài vào app
                cur.execute(s)
                n += 1
        conn.commit()
        print(f"Hoàn tất: đã chạy {n} câu lệnh trên CSDL '{NAME}' (bảng, trigger, dữ liệu mẫu).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
