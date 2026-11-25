# -*- coding: utf-8 -*-
"""Các lớp miền (domain) theo biểu đồ lớp."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional

from .config import SO_LAN_SAI_TOI_DA
from .enums import (GioiTinh, LoaiDiem, TrangThaiDiemDanh, TrangThaiHocSinh,
                    VaiTro, XepLoaiHanhKiem)
from .utils import (LoiNghiepVu, kiem_tra_email, kiem_tra_mat_khau, kiem_tra_sdt,
                    ma_hoa_mat_khau)

# Trọng số từng loại điểm khi tính điểm môn
TRONG_SO_LOAI_DIEM = {LoaiDiem.THUONG_XUYEN: 1, LoaiDiem.GIUA_KY: 2, LoaiDiem.CUOI_KY: 3}


class TaiKhoan:
    def __init__(self, ten_dang_nhap: str, mat_khau_ma_hoa: str, vai_tro: VaiTro,
                 hoat_dong: bool = True, chu_so_huu: "NguoiDung" = None, so_lan_sai: int = 0,
                 lan_dang_nhap_cuoi: str = ""):
        self.ten_dang_nhap = ten_dang_nhap
        self.mat_khau_ma_hoa = mat_khau_ma_hoa
        self.vai_tro = vai_tro
        self.hoat_dong = hoat_dong
        self.chu_so_huu = chu_so_huu          # NguoiDung 1 --- 0..1 TaiKhoan
        self.so_lan_sai = so_lan_sai
        self.lan_dang_nhap_cuoi = lan_dang_nhap_cuoi
        self._dang_nhap = False

    def dang_nhap(self, mat_khau: str = "") -> bool:
        if not self.hoat_dong:
            return False
        if kiem_tra_mat_khau(mat_khau, self.mat_khau_ma_hoa):
            self.so_lan_sai = 0
            self._dang_nhap = True
            return True
        self.so_lan_sai += 1
        if self.so_lan_sai >= SO_LAN_SAI_TOI_DA:
            self.hoat_dong = False            # khóa tài khoản
        return False

    def dang_xuat(self) -> None:
        self._dang_nhap = False

    @property
    def dang_dang_nhap(self) -> bool:
        return self._dang_nhap

    def doi_mat_khau(self, cu: str, moi: str) -> None:
        if not kiem_tra_mat_khau(cu, self.mat_khau_ma_hoa):
            raise LoiNghiepVu("Mật khẩu cũ không đúng.")
        self.dat_mat_khau(moi)

    def dat_mat_khau(self, moi: str) -> None:
        if len(moi) < 6:
            raise LoiNghiepVu("Mật khẩu phải có ít nhất 6 ký tự.")
        self.mat_khau_ma_hoa = ma_hoa_mat_khau(moi)


class NguoiDung(ABC):
    """«abstract» NguoiDung"""

    def __init__(self, ma: str, ho_ten: str, ngay_sinh: Optional[date], gioi_tinh: GioiTinh = GioiTinh.KHAC,
                 dia_chi: str = "", so_dien_thoai: str = "", email: str = ""):
        ma = (ma or "").strip().upper()
        if not ma or not (ho_ten or "").strip():
            raise LoiNghiepVu("Mã và họ tên không được để trống.")
        if not re.fullmatch(r"[A-Z0-9_\-]{2,20}", ma):
            raise LoiNghiepVu("Mã chỉ gồm chữ cái không dấu, chữ số, '-' hoặc '_' (2–20 ký tự).")
        if ngay_sinh is not None and ngay_sinh > date.today():
            raise LoiNghiepVu("Ngày sinh không được ở tương lai.")
        so_dien_thoai = (so_dien_thoai or "").replace(" ", "")
        if so_dien_thoai and not kiem_tra_sdt(so_dien_thoai):
            raise LoiNghiepVu("Số điện thoại không hợp lệ (8-15 chữ số).")
        if email and not kiem_tra_email(email):
            raise LoiNghiepVu("Email không hợp lệ.")
        self.ma = ma
        self.ho_ten = " ".join(ho_ten.split())
        self.ngay_sinh = ngay_sinh
        self.gioi_tinh = gioi_tinh
        self.dia_chi = (dia_chi or "").strip()
        self.so_dien_thoai = so_dien_thoai
        self.email = (email or "").strip()
        self.tai_khoan: Optional[TaiKhoan] = None

    def tinh_tuoi(self) -> Optional[int]:
        if not self.ngay_sinh:
            return None
        h = date.today()
        return h.year - self.ngay_sinh.year - ((h.month, h.day) < (self.ngay_sinh.month, self.ngay_sinh.day))

    @property
    @abstractmethod
    def vai_tro_mac_dinh(self) -> VaiTro: ...


class MonHoc:
    def __init__(self, ma_mon: str, ten_mon: str, so_tin_chi: int = 1, he_so: int = 1):
        self.ma_mon = ma_mon.strip().upper()
        self.ten_mon = ten_mon
        self.so_tin_chi = so_tin_chi
        self.he_so = he_so


class HocKy:
    def __init__(self, ten_hoc_ky: str, ngay_bat_dau: date, ngay_ket_thuc: date):
        self.ten_hoc_ky = ten_hoc_ky
        self.ngay_bat_dau = ngay_bat_dau
        self.ngay_ket_thuc = ngay_ket_thuc
        self.nam_hoc: Optional["NamHoc"] = None

    @property
    def khoa(self) -> str:
        return f"{self.nam_hoc.ten_nam_hoc}|{self.ten_hoc_ky}"

    def __str__(self) -> str:
        return f"{self.ten_hoc_ky} ({self.nam_hoc.ten_nam_hoc})"


class NamHoc:
    """NamHoc ◆— 2..3 HocKy (hợp thành);  NamHoc ◇— LopHoc (tổ chức)."""

    def __init__(self, ten_nam_hoc: str, ngay_bat_dau: date, ngay_ket_thuc: date):
        self.ten_nam_hoc = ten_nam_hoc
        self.ngay_bat_dau = ngay_bat_dau
        self.ngay_ket_thuc = ngay_ket_thuc
        self.hoc_ky: List[HocKy] = []
        self.lop_hoc: List["LopHoc"] = []

    def them_hoc_ky(self, hk: HocKy) -> None:
        if len(self.hoc_ky) >= 3:
            raise LoiNghiepVu("Một năm học chỉ có tối đa 3 học kỳ.")
        hk.nam_hoc = self
        self.hoc_ky.append(hk)

    def hop_le(self) -> bool:
        return 2 <= len(self.hoc_ky) <= 3


class GhiDanh:
    """«association class» giữa HocSinh và LopHoc (lưu lịch sử chuyển lớp)."""

    def __init__(self, hoc_sinh: "HocSinh", lop_hoc: "LopHoc", ngay_vao: date, ngay_ra: Optional[date] = None):
        self.hoc_sinh = hoc_sinh
        self.lop_hoc = lop_hoc
        self.ngay_vao = ngay_vao
        self.ngay_ra = ngay_ra


class PhanCongGiangDay:
    """«association class» giữa GiaoVien, LopHoc và MonHoc."""

    def __init__(self, giao_vien: "GiaoVien", lop_hoc: "LopHoc", mon_hoc: MonHoc,
                 ngay_bat_dau: date, ngay_ket_thuc: Optional[date] = None):
        self.giao_vien = giao_vien
        self.lop_hoc = lop_hoc
        self.mon_hoc = mon_hoc
        self.ngay_bat_dau = ngay_bat_dau
        self.ngay_ket_thuc = ngay_ket_thuc


class LopHoc:
    def __init__(self, ma_lop: str, ten_lop: str, khoi: int, si_so_toi_da: int = 45):
        if si_so_toi_da <= 0:
            raise LoiNghiepVu("Sĩ số tối đa phải lớn hơn 0.")
        self.ma_lop = ma_lop.strip().upper()
        self.ten_lop = ten_lop
        self.khoi = khoi
        self.si_so_toi_da = si_so_toi_da
        self.giao_vien_chu_nhiem: Optional["GiaoVien"] = None   # GiaoVien 1 —chủ nhiệm→ * LopHoc
        self.nam_hoc: Optional[NamHoc] = None
        self.ghi_danh: List[GhiDanh] = []
        self.phan_cong: List[PhanCongGiangDay] = []

    def danh_sach_hoc_sinh(self) -> List["HocSinh"]:
        return [g.hoc_sinh for g in self.ghi_danh if g.ngay_ra is None]

    def dem_si_so(self) -> int:
        return sum(1 for g in self.ghi_danh if g.ngay_ra is None)

    def them_hoc_sinh(self, hs: "HocSinh", ngay_vao: Optional[date] = None) -> GhiDanh:
        if hs in self.danh_sach_hoc_sinh():
            raise LoiNghiepVu(f"{hs.ho_ten} đã ở trong lớp {self.ten_lop}.")
        if self.dem_si_so() >= self.si_so_toi_da:
            raise LoiNghiepVu(f"Lớp {self.ten_lop} đã đủ sĩ số tối đa ({self.si_so_toi_da}).")
        gd = GhiDanh(hs, self, ngay_vao or date.today())
        self.ghi_danh.append(gd)
        hs.ghi_danh.append(gd)
        return gd

    def xoa_hoc_sinh(self, hs: "HocSinh", ngay_ra: Optional[date] = None) -> None:
        """Rời lớp: đóng bản ghi GhiDanh (ngayRa) chứ không xóa để giữ lịch sử."""
        for g in self.ghi_danh:
            if g.hoc_sinh is hs and g.ngay_ra is None:
                g.ngay_ra = ngay_ra or date.today()
                return
        raise LoiNghiepVu(f"{hs.ho_ten} không học lớp {self.ten_lop}.")

    def giao_vien_day(self, mon: MonHoc) -> Optional["GiaoVien"]:
        for p in self.phan_cong:
            if p.mon_hoc is mon and p.ngay_ket_thuc is None:
                return p.giao_vien
        return None


class Diem:
    def __init__(self, hoc_sinh: "HocSinh", mon_hoc: MonHoc, hoc_ky: HocKy,
                 loai_diem: LoaiDiem, gia_tri: float, ngay_nhap: Optional[date] = None):
        if not 0 <= gia_tri <= 10:
            raise LoiNghiepVu("Điểm phải nằm trong khoảng 0–10.")
        self.hoc_sinh = hoc_sinh
        self.mon_hoc = mon_hoc
        self.hoc_ky = hoc_ky
        self.loai_diem = loai_diem
        self.gia_tri = float(gia_tri)
        self.ngay_nhap = ngay_nhap or date.today()


class DiemDanh:
    def __init__(self, hoc_sinh: "HocSinh", lop_hoc: LopHoc, ngay: date,
                 trang_thai: TrangThaiDiemDanh = TrangThaiDiemDanh.CO_MAT, ghi_chu: str = ""):
        self.hoc_sinh = hoc_sinh
        self.lop_hoc = lop_hoc
        self.ngay = ngay
        self.trang_thai = trang_thai
        self.ghi_chu = ghi_chu


class KetQuaHanhKiem:
    def __init__(self, hoc_sinh: "HocSinh", hoc_ky: HocKy, xep_loai: XepLoaiHanhKiem, nhan_xet: str = ""):
        self.hoc_sinh = hoc_sinh
        self.hoc_ky = hoc_ky
        self.xep_loai = xep_loai
        self.nhan_xet = nhan_xet


class HoSoHocSinh:
    """HocSinh 1 ◆— 1 HoSoHocSinh (hợp thành)."""

    def __init__(self, hoc_sinh: "HocSinh", ma_ho_so: str, ghi_chu_suc_khoe: str = "",
                 thanh_tich: str = "", ghi_chu_ky_luat: str = "", ngay_tao: Optional[date] = None):
        self.hoc_sinh = hoc_sinh
        self.ma_ho_so = ma_ho_so
        self.ghi_chu_suc_khoe = ghi_chu_suc_khoe
        self.thanh_tich = thanh_tich
        self.ghi_chu_ky_luat = ghi_chu_ky_luat
        self.ngay_tao = ngay_tao or date.today()

    def cap_nhat_ho_so(self, ghi_chu_suc_khoe: Optional[str] = None, thanh_tich: Optional[str] = None,
                       ghi_chu_ky_luat: Optional[str] = None) -> None:
        if ghi_chu_suc_khoe is not None:
            self.ghi_chu_suc_khoe = ghi_chu_suc_khoe.strip()
        if thanh_tich is not None:
            self.thanh_tich = thanh_tich.strip()
        if ghi_chu_ky_luat is not None:
            self.ghi_chu_ky_luat = ghi_chu_ky_luat.strip()

    def xuat_pdf(self, duong_dan: Optional[str] = None) -> str:
        from .exporters import xuat_pdf_ho_so
        return xuat_pdf_ho_so(self, duong_dan)


class PhuHuynh(NguoiDung):
    def __init__(self, ma, ho_ten, ngay_sinh=None, gioi_tinh=GioiTinh.KHAC, dia_chi="", so_dien_thoai="",
                 email="", quan_he: str = "", nghe_nghiep: str = ""):
        super().__init__(ma, ho_ten, ngay_sinh, gioi_tinh, dia_chi, so_dien_thoai, email)
        self.quan_he = quan_he
        self.nghe_nghiep = nghe_nghiep
        self.hoc_sinh: List["HocSinh"] = []

    @property
    def vai_tro_mac_dinh(self) -> VaiTro:
        return VaiTro.PHU_HUYNH


class GiaoVien(NguoiDung):
    def __init__(self, ma, ho_ten, ngay_sinh=None, gioi_tinh=GioiTinh.KHAC, dia_chi="", so_dien_thoai="",
                 email="", chuyen_mon: str = "", trinh_do: str = ""):
        super().__init__(ma, ho_ten, ngay_sinh, gioi_tinh, dia_chi, so_dien_thoai, email)
        self.ma_giao_vien = self.ma
        self.chuyen_mon = chuyen_mon
        self.trinh_do = trinh_do
        self.lop_chu_nhiem: List[LopHoc] = []
        self.phan_cong: List[PhanCongGiangDay] = []

    @property
    def vai_tro_mac_dinh(self) -> VaiTro:
        return VaiTro.GIAO_VIEN

    def duoc_phu_trach(self, lop: LopHoc) -> bool:
        return lop.giao_vien_chu_nhiem is self or any(
            p.lop_hoc is lop and p.ngay_ket_thuc is None for p in self.phan_cong)

    def duoc_day_mon(self, lop: LopHoc, mon: MonHoc) -> bool:
        return any(p.lop_hoc is lop and p.mon_hoc is mon and p.ngay_ket_thuc is None for p in self.phan_cong)

    def nhap_diem(self, hs: "HocSinh", mon: MonHoc, hoc_ky: HocKy, loai: LoaiDiem, diem: float) -> Diem:
        d = Diem(hs, mon, hoc_ky, loai, diem)            # kiểm tra 0–10 trong Diem
        if loai is not LoaiDiem.THUONG_XUYEN:            # GK/CK chỉ có một cột điểm -> ghi đè
            hs.diem = [x for x in hs.diem if not (x.mon_hoc is mon and x.hoc_ky is hoc_ky and x.loai_diem is loai)]
        hs.diem.append(d)
        return d

    def luu_bang_diem(self, hs: "HocSinh", mon: MonHoc, hoc_ky: HocKy, thuong_xuyen: List[float],
                      giua_ky: Optional[float], cuoi_ky: Optional[float]) -> None:
        """Thay toàn bộ điểm của (học sinh, môn, học kỳ) bằng dữ liệu của bảng điểm lớp."""
        hs.diem = [x for x in hs.diem if not (x.mon_hoc is mon and x.hoc_ky is hoc_ky)]
        for v in thuong_xuyen:
            hs.diem.append(Diem(hs, mon, hoc_ky, LoaiDiem.THUONG_XUYEN, v))
        if giua_ky is not None:
            hs.diem.append(Diem(hs, mon, hoc_ky, LoaiDiem.GIUA_KY, giua_ky))
        if cuoi_ky is not None:
            hs.diem.append(Diem(hs, mon, hoc_ky, LoaiDiem.CUOI_KY, cuoi_ky))

    def diem_danh(self, lop: LopHoc, ngay: date,
                  trang_thai: Optional[Dict[str, TrangThaiDiemDanh]] = None,
                  ghi_chu: Optional[Dict[str, str]] = None) -> List[DiemDanh]:
        """Điểm danh cả lớp. Học sinh không có trong `trang_thai` mặc định CO_MAT."""
        trang_thai, ghi_chu, kq = trang_thai or {}, ghi_chu or {}, []
        for hs in lop.danh_sach_hoc_sinh():
            hs.diem_danh = [x for x in hs.diem_danh if not (x.lop_hoc is lop and x.ngay == ngay)]
            dd = DiemDanh(hs, lop, ngay, trang_thai.get(hs.ma, TrangThaiDiemDanh.CO_MAT), ghi_chu.get(hs.ma, ""))
            hs.diem_danh.append(dd)
            kq.append(dd)
        return kq


class HocSinh(NguoiDung):
    def __init__(self, ma, ho_ten, ngay_sinh, gioi_tinh=GioiTinh.KHAC, dia_chi="", so_dien_thoai="",
                 email="", ngay_nhap_hoc: Optional[date] = None,
                 trang_thai: TrangThaiHocSinh = TrangThaiHocSinh.DANG_HOC,
                 noi_sinh: str = "", dan_toc: str = "Kinh", so_cccd: str = ""):
        super().__init__(ma, ho_ten, ngay_sinh, gioi_tinh, dia_chi, so_dien_thoai, email)
        if ngay_sinh is None:
            raise LoiNghiepVu("Học sinh phải có ngày sinh.")
        so_cccd = (so_cccd or "").strip()
        if so_cccd and not re.fullmatch(r"\d{9}|\d{12}", so_cccd):
            raise LoiNghiepVu("Số CMND/CCCD phải gồm 9 hoặc 12 chữ số.")
        self.ma_hoc_sinh = self.ma
        self.ngay_nhap_hoc = ngay_nhap_hoc or date.today()
        self.trang_thai = trang_thai
        self.noi_sinh = (noi_sinh or "").strip()
        self.dan_toc = (dan_toc or "").strip()
        self.so_cccd = so_cccd
        self.ho_so = HoSoHocSinh(self, "HS-" + self.ma_hoc_sinh)        # hợp thành 1-1
        self.phu_huynh: List[PhuHuynh] = []                              # 1..*
        self.ghi_danh: List[GhiDanh] = []
        self.diem: List[Diem] = []
        self.diem_danh: List[DiemDanh] = []
        self.ket_qua_hanh_kiem: List[KetQuaHanhKiem] = []

    @property
    def vai_tro_mac_dinh(self) -> VaiTro:
        return VaiTro.HOC_SINH

    @property
    def lop_hien_tai(self) -> Optional[LopHoc]:
        for g in reversed(self.ghi_danh):
            if g.ngay_ra is None:
                return g.lop_hoc
        return None

    def them_phu_huynh(self, ph: PhuHuynh) -> None:
        if ph not in self.phu_huynh:
            self.phu_huynh.append(ph)
            ph.hoc_sinh.append(self)

    def nhap_hoc(self, lop: LopHoc, ngay_vao: Optional[date] = None) -> None:
        if self.lop_hien_tai is not None:
            raise LoiNghiepVu("Học sinh đã có lớp, hãy dùng chuyển lớp.")
        lop.them_hoc_sinh(self, ngay_vao)

    def chuyen_lop(self, lop_moi: LopHoc, ngay: Optional[date] = None) -> None:
        cu = self.lop_hien_tai
        if cu is None:
            raise LoiNghiepVu("Học sinh chưa có lớp, hãy dùng nhập học.")
        if cu is lop_moi:
            raise LoiNghiepVu("Lớp mới trùng lớp hiện tại.")
        if lop_moi.dem_si_so() >= lop_moi.si_so_toi_da:       # kiểm tra trước khi rời lớp cũ
            raise LoiNghiepVu(f"Lớp {lop_moi.ten_lop} đã đủ sĩ số.")
        cu.xoa_hoc_sinh(self, ngay)
        lop_moi.them_hoc_sinh(self, ngay)

    # ---------- điểm ----------
    def diem_mon(self, mon: MonHoc, hoc_ky: HocKy) -> Optional[float]:
        ds = [d for d in self.diem if d.mon_hoc is mon and d.hoc_ky is hoc_ky]
        if not ds:
            return None
        tong_tr = sum(TRONG_SO_LOAI_DIEM[d.loai_diem] for d in ds)
        return sum(d.gia_tri * TRONG_SO_LOAI_DIEM[d.loai_diem] for d in ds) / tong_tr

    def tinh_diem_trung_binh(self, hoc_ky: HocKy) -> float:
        """Trung bình các môn có điểm, có nhân hệ số môn (MonHoc.heSo)."""
        tong, tong_he_so = 0.0, 0
        for mon in {d.mon_hoc for d in self.diem if d.hoc_ky is hoc_ky}:
            tong += self.diem_mon(mon, hoc_ky) * mon.he_so
            tong_he_so += mon.he_so
        return round(tong / tong_he_so, 2) if tong_he_so else 0.0

    def tinh_diem_ca_nam(self, nam_hoc: NamHoc) -> float:
        """Điểm trung bình cả năm = (HK1 + 2×HK2) / 3 (chỉ tính học kỳ đã có điểm)."""
        tong, tr = 0.0, 0
        for i, hk in enumerate(nam_hoc.hoc_ky):
            dtb = self.tinh_diem_trung_binh(hk)
            if dtb:
                w = 2 if i == 1 else 1
                tong += dtb * w
                tr += w
        return round(tong / tr, 2) if tr else 0.0

    def hanh_kiem_hoc_ky(self, hoc_ky: HocKy) -> Optional[KetQuaHanhKiem]:
        return next((k for k in self.ket_qua_hanh_kiem if k.hoc_ky is hoc_ky), None)

    # ---------- điểm danh ----------
    def thong_ke_diem_danh(self, tu: Optional[date] = None, den: Optional[date] = None,
                           lop: Optional[LopHoc] = None) -> Dict[TrangThaiDiemDanh, int]:
        kq = {t: 0 for t in TrangThaiDiemDanh}
        for d in self.diem_danh:
            if (tu and d.ngay < tu) or (den and d.ngay > den) or (lop and d.lop_hoc is not lop):
                continue
            kq[d.trang_thai] += 1
        return kq
