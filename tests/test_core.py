# -*- coding: utf-8 -*-
"""Kiểm thử phần lõi (không cần giao diện):  python -m unittest discover -s tests -v"""
import csv
import json
import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.enums import GioiTinh, LoaiDiem, TrangThaiDiemDanh, TrangThaiHocSinh, XepLoaiHanhKiem
from app.models import HocSinh, PhuHuynh
from app.services import HeThong
from app.utils import LoiNghiepVu


class Co(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.db = os.path.join(self.d, "hocsinh.db")
        self.ht = HeThong(self.db)
        self.ht.dang_nhap("admin", "admin123")

    def mo_lai(self):
        self.ht.dong()
        return HeThong(self.db)

    def test_du_lieu_mau(self):
        t = self.ht.thong_tin_he_thong()
        self.assertGreaterEqual(t["so_hs"], 300)
        self.assertEqual(self.ht.hoc_sinh["HS001"].ho_ten, "Nguyễn Minh An")
        self.assertEqual(self.ht.hoc_sinh["HS001"].lop_hien_tai.ma_lop, "10A1")

    def test_luu_ben_vung_sau_khi_thoat(self):
        hs = HocSinh("HS900", "Trần Văn Kiểm Thử", date(2010, 1, 2), GioiTinh.NAM)
        ph = self.ht.tao_phu_huynh_moi([{"ho_ten": "Trần Văn Bố", "quan_he": "Bố", "sdt": "0911222333"}])
        tk = self.ht.them_ho_so_hoc_sinh(hs, self.ht.lop_hoc["10A2"], ph, tao_tk_hs=True)
        self.assertEqual(tk[0][0], "hs900")
        ht2 = self.mo_lai()
        h = ht2.hoc_sinh["HS900"]
        self.assertEqual(h.lop_hien_tai.ma_lop, "10A2")
        self.assertEqual(h.phu_huynh[0].ho_ten, "Trần Văn Bố")
        self.assertTrue(ht2.dang_nhap("hs900", "123456"))

    def test_diem_diem_danh_hanh_kiem_ben_vung(self):
        lop, mon, hk = self.ht.lop_hoc["10A1"], self.ht.mon_hoc["TOAN"], self.ht.hoc_ky_hien_tai()
        self.ht.dang_xuat()
        self.ht.dang_nhap("gv01", "gv123")
        du_lieu = {"HS001": {"tx": [8, 9, 10, 7], "gk": 9.0, "ck": None}}
        self.ht.luu_bang_diem_lop(lop, mon, hk, du_lieu)
        self.ht.luu_diem_danh(lop, date(2026, 11, 20), {"HS001": TrangThaiDiemDanh.VANG_CO_PHEP}, {"HS001": "Ốm"})
        self.ht.luu_hanh_kiem_lop(lop, hk, {"HS001": (XepLoaiHanhKiem.TOT, "ok")})
        h = self.mo_lai().hoc_sinh["HS001"]
        tx = [d.gia_tri for d in h.diem if d.mon_hoc.ma_mon == "TOAN" and d.hoc_ky.ten_hoc_ky == hk.ten_hoc_ky
              and d.loai_diem is LoaiDiem.THUONG_XUYEN]
        self.assertEqual(tx, [8, 9, 10, 7])                 # đúng thứ tự TX1..TX4
        dd = [x for x in h.diem_danh if x.ngay == date(2026, 11, 20)]
        self.assertEqual(dd[0].trang_thai, TrangThaiDiemDanh.VANG_CO_PHEP)
        self.assertEqual(h.ket_qua_hanh_kiem[0].xep_loai, XepLoaiHanhKiem.TOT)

    def test_phan_quyen_giao_vien(self):
        self.ht.dang_xuat()
        self.ht.dang_nhap("gv01", "gv123")
        with self.assertRaises(LoiNghiepVu):                # gv01 không dạy 12A3
            self.ht.luu_bang_diem_lop(self.ht.lop_hoc["12A3"], self.ht.mon_hoc["TOAN"], self.ht.hoc_ky_hien_tai(), {})
        with self.assertRaises(LoiNghiepVu):
            self.ht.luu_hanh_kiem_lop(self.ht.lop_hoc["10A2"], self.ht.hoc_ky_hien_tai(), {})

    def test_khoa_tai_khoan_sau_5_lan_sai(self):
        self.ht.dang_xuat()
        for _ in range(5):
            with self.assertRaises(LoiNghiepVu):
                self.ht.dang_nhap("hs002", "sai")
        with self.assertRaises(LoiNghiepVu):
            self.ht.dang_nhap("hs002", "hs123")
        self.assertFalse(self.mo_lai().tai_khoan["hs002"].hoat_dong)      # trạng thái khóa được lưu

    def test_chuyen_lop_va_trang_thai(self):
        hs = self.ht.hoc_sinh["HS001"]
        self.ht.chuyen_lop(hs, self.ht.lop_hoc["10A2"])
        h = self.mo_lai().hoc_sinh["HS001"]
        self.assertEqual(h.lop_hien_tai.ma_lop, "10A2")
        self.assertEqual(len(h.ghi_danh), 2)

    def test_khong_xoa_ho_so_da_co_diem(self):
        with self.assertRaises(LoiNghiepVu):
            self.ht.xoa_ho_so(self.ht.hoc_sinh["HS001"])

    def test_csv_xuat_nhap(self):
        f = os.path.join(self.d, "mau.csv")
        self.ht.xuat_csv_mau(f)
        ok, loi = self.ht.nhap_csv(f)
        self.assertEqual((ok, loi), (2, []))
        ok, loi = self.ht.nhap_csv(f)                        # nhập lại -> trùng mã
        self.assertEqual(ok, 0)
        self.assertEqual(len(loi), 2)
        self.assertIn("HS900", self.mo_lai().hoc_sinh)

    def test_sao_luu_va_phuc_hoi(self):
        p = self.ht.sao_luu_ngay()
        self.ht.hoc_sinh["HS001"].ho_ten = "Đã Sửa"
        self.ht.luu_du_lieu()
        self.ht.phuc_hoi(p)
        self.assertEqual(self.ht.hoc_sinh["HS001"].ho_ten, "Nguyễn Minh An")
        with self.assertRaises(LoiNghiepVu):
            self.ht.phuc_hoi(self.db + "-khong-co")

    def test_tu_phuc_hoi_khi_tep_hong(self):
        self.ht.sao_luu_ngay()
        self.ht.dong()
        with open(self.db, "wb") as f:
            f.write(b"day khong phai sqlite" * 100)
        ht2 = HeThong(self.db)
        self.assertGreaterEqual(len(ht2.hoc_sinh), 300)
        self.assertTrue(ht2.thong_bao_khoi_dong)

    def test_nhap_du_lieu_cu(self):
        cu = {"hoc_sinh": [{"ma": "HS777", "ho_ten": "Lê Cũ", "ngay_sinh": "01/02/2010", "gioi_tinh": "NAM",
                            "trang_thai": "DANG_HOC", "phu_huynh": ["PH777"], "ghi_danh": [{"lop": "10A1", "vao": "05/09/2026", "ra": ""}],
                            "diem": [{"mon": "TOAN", "hoc_ky": self.ht.hoc_ky_hien_tai().khoa, "loai": "GIUA_KY", "gia_tri": 8, "ngay": "01/10/2026"}]}],
              "phu_huynh": [{"ma": "PH777", "ho_ten": "Lê Bố", "gioi_tinh": "NAM", "quan_he": "Bố"}]}
        f = os.path.join(self.d, "hocsinh.txt")
        json.dump(cu, open(f, "w", encoding="utf-8"))
        self.ht.nhap_du_lieu_cu(f)
        h = self.mo_lai().hoc_sinh["HS777"]
        self.assertEqual(h.lop_hien_tai.ma_lop, "10A1")
        self.assertEqual(len(h.diem), 1)

    def test_tong_quan_bao_cao(self):
        tq = self.ht.tong_quan()
        self.assertEqual(sum(tq["phan_bo_hoc_luc"].values()), tq["so_hs_dang_hoc"])
        from app.reports import DichVuBaoCao
        hk = self.ht.hoc_ky_hien_tai()
        for s in (DichVuBaoCao.bao_cao_lop(self.ht.lop_hoc["10A1"], hk),
                  DichVuBaoCao.bao_cao_mon(self.ht.lop_hoc["10A1"], self.ht.mon_hoc["TOAN"], hk),
                  DichVuBaoCao.bao_cao_diem_danh(self.ht.lop_hoc["10A1"], hk),
                  DichVuBaoCao.bao_cao_hoc_sinh(self.ht.hoc_sinh["HS001"], hk),
                  DichVuBaoCao.thong_ke(list(self.ht.hoc_sinh.values()), list(self.ht.lop_hoc.values()), hk)):
            self.assertTrue(len(s) > 50)

    def test_xuat_pdf_html(self):
        from app.exporters import xuat_html_ho_so
        h = self.ht.hoc_sinh["HS001"]
        self.assertTrue(os.path.getsize(h.ho_so.xuat_pdf(os.path.join(self.d, "a.pdf"))) > 300)
        xuat_html_ho_so(h, os.path.join(self.d, "a.html"), self.ht.hoc_ky_hien_tai())
        self.assertIn("Nguyễn Minh An", open(os.path.join(self.d, "a.html"), encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
