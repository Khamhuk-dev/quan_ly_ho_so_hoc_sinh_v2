# -*- coding: utf-8 -*-
"""Lưu trữ bền vững bằng SQLite (thư viện chuẩn của Python, không cần cài thêm).

Dữ liệu được ghi xuống đĩa NGAY SAU MỖI THAO TÁC (transaction an toàn: mất điện giữa chừng
cũng không hỏng dữ liệu) và có bản sao lưu tự động mỗi khi mở chương trình.
"""
from __future__ import annotations

import glob
import os
import shutil
import sqlite3
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

from .config import SO_BAN_SAO_LUU_TOI_DA, SO_DONG_NHAT_KY_TOI_DA
from .enums import (GioiTinh, LoaiDiem, TrangThaiDiemDanh, TrangThaiHocSinh, VaiTro, XepLoaiHanhKiem)
from .models import (Diem, DiemDanh, GhiDanh, GiaoVien, HoSoHocSinh, HocKy, HocSinh, KetQuaHanhKiem,
                     LopHoc, MonHoc, NamHoc, PhanCongGiangDay, PhuHuynh, TaiKhoan)
from .utils import iso, tu_iso

PHIEN_BAN_CSDL = 1
CAC_PHAN = ("danh_muc", "nguoi", "tai_khoan", "diem", "diem_danh", "hanh_kiem")

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS mon_hoc (ma_mon TEXT PRIMARY KEY, ten_mon TEXT, so_tin_chi INTEGER, he_so INTEGER);
CREATE TABLE IF NOT EXISTS nam_hoc (ten TEXT PRIMARY KEY, bat_dau TEXT, ket_thuc TEXT);
CREATE TABLE IF NOT EXISTS hoc_ky (nam_hoc TEXT, ten TEXT, bat_dau TEXT, ket_thuc TEXT, PRIMARY KEY (nam_hoc, ten));
CREATE TABLE IF NOT EXISTS giao_vien (ma TEXT PRIMARY KEY, ho_ten TEXT, ngay_sinh TEXT, gioi_tinh TEXT,
    dia_chi TEXT, sdt TEXT, email TEXT, chuyen_mon TEXT, trinh_do TEXT);
CREATE TABLE IF NOT EXISTS lop_hoc (ma_lop TEXT PRIMARY KEY, ten_lop TEXT, khoi INTEGER, si_so_toi_da INTEGER,
    gvcn TEXT, nam_hoc TEXT);
CREATE TABLE IF NOT EXISTS phan_cong (gv TEXT, lop TEXT, mon TEXT, bat_dau TEXT, ket_thuc TEXT);
CREATE TABLE IF NOT EXISTS phu_huynh (ma TEXT PRIMARY KEY, ho_ten TEXT, ngay_sinh TEXT, gioi_tinh TEXT,
    dia_chi TEXT, sdt TEXT, email TEXT, quan_he TEXT, nghe_nghiep TEXT);
CREATE TABLE IF NOT EXISTS hoc_sinh (ma TEXT PRIMARY KEY, ho_ten TEXT, ngay_sinh TEXT, gioi_tinh TEXT,
    dia_chi TEXT, sdt TEXT, email TEXT, ngay_nhap_hoc TEXT, trang_thai TEXT, noi_sinh TEXT, dan_toc TEXT,
    so_cccd TEXT, ma_ho_so TEXT, suc_khoe TEXT, thanh_tich TEXT, ky_luat TEXT, ngay_tao_ho_so TEXT);
CREATE TABLE IF NOT EXISTS hs_ph (ma_hs TEXT, ma_ph TEXT);
CREATE TABLE IF NOT EXISTS ghi_danh (ma_hs TEXT, ma_lop TEXT, vao TEXT, ra TEXT);
CREATE TABLE IF NOT EXISTS tai_khoan (ten TEXT PRIMARY KEY, mat_khau TEXT, vai_tro TEXT, hoat_dong INTEGER,
    chu_so_huu TEXT, so_lan_sai INTEGER, dang_nhap_cuoi TEXT);
CREATE TABLE IF NOT EXISTS diem (ma_hs TEXT, mon TEXT, hoc_ky TEXT, loai TEXT, gia_tri REAL, ngay TEXT);
CREATE TABLE IF NOT EXISTS diem_danh (ma_hs TEXT, lop TEXT, ngay TEXT, trang_thai TEXT, ghi_chu TEXT);
CREATE TABLE IF NOT EXISTS hanh_kiem (ma_hs TEXT, hoc_ky TEXT, xep_loai TEXT, nhan_xet TEXT);
CREATE TABLE IF NOT EXISTS nhat_ky (id INTEGER PRIMARY KEY AUTOINCREMENT, thoi_gian TEXT, nguoi TEXT,
    hanh_dong TEXT, chi_tiet TEXT);
CREATE INDEX IF NOT EXISTS ix_diem_hs ON diem(ma_hs);
CREATE INDEX IF NOT EXISTS ix_dd_hs ON diem_danh(ma_hs);
"""

BANG_BAT_BUOC = ("meta", "mon_hoc", "nam_hoc", "hoc_ky", "giao_vien", "lop_hoc", "hoc_sinh", "tai_khoan")


def kiem_tra_tep_csdl(duong_dan: str) -> bool:
    """True nếu là tệp SQLite hợp lệ của chương trình này."""
    try:
        c = sqlite3.connect(f"file:{duong_dan}?mode=ro", uri=True)
        try:
            ten = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            c.execute("PRAGMA integrity_check").fetchone()
        finally:
            c.close()
        return all(b in ten for b in BANG_BAT_BUOC)
    except sqlite3.Error:
        return False


class KhoSQLite:
    def __init__(self, duong_dan: str):
        self.duong_dan = duong_dan
        self.conn = sqlite3.connect(duong_dan)
        self.conn.execute("PRAGMA synchronous=FULL")
        self.conn.executescript(SCHEMA)
        self.conn.execute("INSERT OR IGNORE INTO meta VALUES ('phien_ban', ?)", (str(PHIEN_BAN_CSDL),))
        self.conn.execute("INSERT OR IGNORE INTO meta VALUES ('tao_luc', ?)", (datetime.now().isoformat(timespec="seconds"),))
        self.conn.commit()

    def dong(self) -> None:
        try:
            self.conn.commit()
            self.conn.close()
        except sqlite3.Error:
            pass

    def co_du_lieu(self) -> bool:
        return self.conn.execute("SELECT COUNT(*) FROM tai_khoan").fetchone()[0] > 0

    # ------------------------------------------------------------------ GHI
    def luu(self, ht, phan: Optional[Iterable[str]] = None) -> None:
        phan = set(phan) if phan else set(CAC_PHAN)
        c = self.conn
        with c:
            if "danh_muc" in phan:
                for b in ("mon_hoc", "nam_hoc", "hoc_ky", "giao_vien", "lop_hoc", "phan_cong"):
                    c.execute(f"DELETE FROM {b}")
                c.executemany("INSERT INTO mon_hoc VALUES (?,?,?,?)",
                              [(m.ma_mon, m.ten_mon, m.so_tin_chi, m.he_so) for m in ht.mon_hoc.values()])
                c.executemany("INSERT INTO nam_hoc VALUES (?,?,?)",
                              [(n.ten_nam_hoc, iso(n.ngay_bat_dau), iso(n.ngay_ket_thuc)) for n in ht.nam_hoc.values()])
                c.executemany("INSERT INTO hoc_ky VALUES (?,?,?,?)",
                              [(n.ten_nam_hoc, k.ten_hoc_ky, iso(k.ngay_bat_dau), iso(k.ngay_ket_thuc))
                               for n in ht.nam_hoc.values() for k in n.hoc_ky])
                c.executemany("INSERT INTO giao_vien VALUES (?,?,?,?,?,?,?,?,?)",
                              [(g.ma, g.ho_ten, iso(g.ngay_sinh), g.gioi_tinh.name, g.dia_chi, g.so_dien_thoai,
                                g.email, g.chuyen_mon, g.trinh_do) for g in ht.giao_vien.values()])
                c.executemany("INSERT INTO lop_hoc VALUES (?,?,?,?,?,?)",
                              [(l.ma_lop, l.ten_lop, l.khoi, l.si_so_toi_da,
                                l.giao_vien_chu_nhiem.ma if l.giao_vien_chu_nhiem else "",
                                l.nam_hoc.ten_nam_hoc if l.nam_hoc else "") for l in ht.lop_hoc.values()])
                c.executemany("INSERT INTO phan_cong VALUES (?,?,?,?,?)",
                              [(p.giao_vien.ma, p.lop_hoc.ma_lop, p.mon_hoc.ma_mon, iso(p.ngay_bat_dau),
                                iso(p.ngay_ket_thuc)) for p in ht.phan_cong])
            if "nguoi" in phan:
                for b in ("phu_huynh", "hoc_sinh", "hs_ph", "ghi_danh"):
                    c.execute(f"DELETE FROM {b}")
                c.executemany("INSERT INTO phu_huynh VALUES (?,?,?,?,?,?,?,?,?)",
                              [(p.ma, p.ho_ten, iso(p.ngay_sinh), p.gioi_tinh.name, p.dia_chi, p.so_dien_thoai,
                                p.email, p.quan_he, p.nghe_nghiep) for p in ht.phu_huynh.values()])
                c.executemany("INSERT INTO hoc_sinh VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              [(h.ma, h.ho_ten, iso(h.ngay_sinh), h.gioi_tinh.name, h.dia_chi, h.so_dien_thoai,
                                h.email, iso(h.ngay_nhap_hoc), h.trang_thai.name, h.noi_sinh, h.dan_toc, h.so_cccd,
                                h.ho_so.ma_ho_so, h.ho_so.ghi_chu_suc_khoe, h.ho_so.thanh_tich,
                                h.ho_so.ghi_chu_ky_luat, iso(h.ho_so.ngay_tao)) for h in ht.hoc_sinh.values()])
                c.executemany("INSERT INTO hs_ph VALUES (?,?)",
                              [(h.ma, p.ma) for h in ht.hoc_sinh.values() for p in h.phu_huynh])
                c.executemany("INSERT INTO ghi_danh VALUES (?,?,?,?)",
                              [(h.ma, g.lop_hoc.ma_lop, iso(g.ngay_vao), iso(g.ngay_ra))
                               for h in ht.hoc_sinh.values() for g in h.ghi_danh])
            if "tai_khoan" in phan:
                c.execute("DELETE FROM tai_khoan")
                c.executemany("INSERT INTO tai_khoan VALUES (?,?,?,?,?,?,?)",
                              [(t.ten_dang_nhap, t.mat_khau_ma_hoa, t.vai_tro.name, int(t.hoat_dong),
                                t.chu_so_huu.ma, t.so_lan_sai, t.lan_dang_nhap_cuoi) for t in ht.tai_khoan.values()])
            if "diem" in phan:
                c.execute("DELETE FROM diem")
                c.executemany("INSERT INTO diem VALUES (?,?,?,?,?,?)",
                              [(h.ma, x.mon_hoc.ma_mon, x.hoc_ky.khoa, x.loai_diem.name, x.gia_tri, iso(x.ngay_nhap))
                               for h in ht.hoc_sinh.values() for x in h.diem])
            if "diem_danh" in phan:
                c.execute("DELETE FROM diem_danh")
                c.executemany("INSERT INTO diem_danh VALUES (?,?,?,?,?)",
                              [(h.ma, x.lop_hoc.ma_lop, iso(x.ngay), x.trang_thai.name, x.ghi_chu)
                               for h in ht.hoc_sinh.values() for x in h.diem_danh])
            if "hanh_kiem" in phan:
                c.execute("DELETE FROM hanh_kiem")
                c.executemany("INSERT INTO hanh_kiem VALUES (?,?,?,?)",
                              [(h.ma, x.hoc_ky.khoa, x.xep_loai.name, x.nhan_xet)
                               for h in ht.hoc_sinh.values() for x in h.ket_qua_hanh_kiem])

    # ------------------------------------------------------------------ ĐỌC
    def doc(self, ht) -> None:
        c = self.conn
        for ma, ten, tc, hs in c.execute("SELECT * FROM mon_hoc"):
            ht.mon_hoc[ma] = MonHoc(ma, ten, tc, hs)
        for ten, bd, kt in c.execute("SELECT * FROM nam_hoc ORDER BY bat_dau"):
            nh = NamHoc(ten, tu_iso(bd), tu_iso(kt))
            for _, tk, hbd, hkt in c.execute("SELECT * FROM hoc_ky WHERE nam_hoc=? ORDER BY bat_dau", (ten,)):
                nh.them_hoc_ky(HocKy(tk, tu_iso(hbd), tu_iso(hkt)))
            ht.nam_hoc[ten] = nh
        hk_khoa = {k.khoa: k for k in ht.hoc_ky_tat_ca()}
        for r in c.execute("SELECT * FROM giao_vien"):
            ht.giao_vien[r[0]] = GiaoVien(r[0], r[1], tu_iso(r[2]), GioiTinh[r[3]], r[4], r[5], r[6], r[7], r[8])
        for ma, ten, khoi, ss, gvcn, nam in c.execute("SELECT * FROM lop_hoc"):
            lop = LopHoc(ma, ten, khoi, ss)
            if gvcn in ht.giao_vien:
                lop.giao_vien_chu_nhiem = ht.giao_vien[gvcn]
                ht.giao_vien[gvcn].lop_chu_nhiem.append(lop)
            if nam in ht.nam_hoc:
                lop.nam_hoc = ht.nam_hoc[nam]
                lop.nam_hoc.lop_hoc.append(lop)
            ht.lop_hoc[lop.ma_lop] = lop
        for r in c.execute("SELECT * FROM phu_huynh"):
            ht.phu_huynh[r[0]] = PhuHuynh(r[0], r[1], tu_iso(r[2]), GioiTinh[r[3]], r[4], r[5], r[6], r[7], r[8])
        for r in c.execute("SELECT * FROM hoc_sinh"):
            h = HocSinh(r[0], r[1], tu_iso(r[2]), GioiTinh[r[3]], r[4], r[5], r[6], tu_iso(r[7]),
                        TrangThaiHocSinh[r[8]], r[9], r[10], r[11])
            h.ho_so = HoSoHocSinh(h, r[12], r[13], r[14], r[15], tu_iso(r[16]))
            ht.hoc_sinh[h.ma] = h
        for ma_hs, ma_ph in c.execute("SELECT * FROM hs_ph"):
            if ma_hs in ht.hoc_sinh and ma_ph in ht.phu_huynh:
                ht.hoc_sinh[ma_hs].them_phu_huynh(ht.phu_huynh[ma_ph])
        for ma_hs, ma_lop, vao, ra in c.execute("SELECT * FROM ghi_danh"):
            h, lop = ht.hoc_sinh.get(ma_hs), ht.lop_hoc.get(ma_lop)
            if h and lop:
                gd = GhiDanh(h, lop, tu_iso(vao), tu_iso(ra))
                h.ghi_danh.append(gd)
                lop.ghi_danh.append(gd)
        for ma_hs, mon, hk, loai, gt, ngay in c.execute("SELECT * FROM diem"):
            h = ht.hoc_sinh.get(ma_hs)
            if h and mon in ht.mon_hoc and hk in hk_khoa:
                h.diem.append(Diem(h, ht.mon_hoc[mon], hk_khoa[hk], LoaiDiem[loai], gt, tu_iso(ngay)))
        for ma_hs, lop, ngay, tt, gc in c.execute("SELECT * FROM diem_danh"):
            h = ht.hoc_sinh.get(ma_hs)
            if h and lop in ht.lop_hoc:
                h.diem_danh.append(DiemDanh(h, ht.lop_hoc[lop], tu_iso(ngay), TrangThaiDiemDanh[tt], gc))
        for ma_hs, hk, xl, nx in c.execute("SELECT * FROM hanh_kiem"):
            h = ht.hoc_sinh.get(ma_hs)
            if h and hk in hk_khoa:
                h.ket_qua_hanh_kiem.append(KetQuaHanhKiem(h, hk_khoa[hk], XepLoaiHanhKiem[xl], nx))
        for gv, lop, mon, bd, kt in c.execute("SELECT * FROM phan_cong"):
            if gv in ht.giao_vien and lop in ht.lop_hoc and mon in ht.mon_hoc:
                pc = PhanCongGiangDay(ht.giao_vien[gv], ht.lop_hoc[lop], ht.mon_hoc[mon], tu_iso(bd), tu_iso(kt))
                ht.phan_cong.append(pc)
                pc.giao_vien.phan_cong.append(pc)
                pc.lop_hoc.phan_cong.append(pc)
        for ten, mk, vt, hd, chu, sai, cuoi in c.execute("SELECT * FROM tai_khoan"):
            nguoi = ht.nguoi_theo_ma(chu)
            if nguoi is None:
                continue
            tk = TaiKhoan(ten, mk, VaiTro[vt], bool(hd), nguoi, sai, cuoi or "")
            nguoi.tai_khoan = tk
            ht.tai_khoan[ten] = tk

    # ------------------------------------------------------------------ NHẬT KÝ
    def ghi_nhat_ky(self, nguoi: str, hanh_dong: str, chi_tiet: str = "") -> None:
        with self.conn:
            self.conn.execute("INSERT INTO nhat_ky (thoi_gian, nguoi, hanh_dong, chi_tiet) VALUES (?,?,?,?)",
                              (datetime.now().isoformat(sep=" ", timespec="seconds"), nguoi, hanh_dong, chi_tiet))
            self.conn.execute("DELETE FROM nhat_ky WHERE id <= (SELECT MAX(id) FROM nhat_ky) - ?",
                              (SO_DONG_NHAT_KY_TOI_DA,))

    def doc_nhat_ky(self, gioi_han: int = 500, tu_khoa: str = "") -> List[Tuple[str, str, str, str]]:
        if tu_khoa:
            k = f"%{tu_khoa}%"
            cur = self.conn.execute("SELECT thoi_gian, nguoi, hanh_dong, chi_tiet FROM nhat_ky WHERE nguoi LIKE ? OR "
                                    "hanh_dong LIKE ? OR chi_tiet LIKE ? ORDER BY id DESC LIMIT ?", (k, k, k, gioi_han))
        else:
            cur = self.conn.execute("SELECT thoi_gian, nguoi, hanh_dong, chi_tiet FROM nhat_ky ORDER BY id DESC LIMIT ?",
                                    (gioi_han,))
        return cur.fetchall()

    # ------------------------------------------------------------------ SAO LƯU
    def sao_luu(self, thu_muc: str, ly_do: str = "thu_cong") -> str:
        os.makedirs(thu_muc, exist_ok=True)
        ten = f"hocsinh_{datetime.now():%Y%m%d_%H%M%S}_{ly_do}.db"
        dich_path = os.path.join(thu_muc, ten)
        dich = sqlite3.connect(dich_path)
        try:
            self.conn.commit()
            self.conn.backup(dich)
        finally:
            dich.close()
        self.don_sao_luu_cu(thu_muc)
        return dich_path

    @staticmethod
    def danh_sach_sao_luu(thu_muc: str) -> List[str]:
        return sorted(glob.glob(os.path.join(thu_muc, "hocsinh_*.db")), reverse=True)

    @staticmethod
    def don_sao_luu_cu(thu_muc: str) -> None:
        for f in KhoSQLite.danh_sach_sao_luu(thu_muc)[SO_BAN_SAO_LUU_TOI_DA:]:
            try:
                os.remove(f)
            except OSError:
                pass

    def dung_luong(self) -> int:
        try:
            return os.path.getsize(self.duong_dan)
        except OSError:
            return 0
