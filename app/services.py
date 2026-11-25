# -*- coding: utf-8 -*-
"""HeThong: toàn bộ nghiệp vụ (đăng nhập, phân quyền, hồ sơ, điểm, điểm danh, quản trị, sao lưu...)."""
from __future__ import annotations

import csv
import os
import shutil
import sqlite3
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from .config import (DUONG_DAN_DB, MAT_KHAU_MAC_DINH, SO_BAN_SAO_LUU_TOI_DA, TEN_UNG_DUNG)
from .enums import (GioiTinh, LoaiDiem, TrangThaiDiemDanh, TrangThaiHocSinh, VaiTro, XepLoaiHanhKiem)
from .models import (GiaoVien, HocKy, HocSinh, KetQuaHanhKiem, LopHoc, MonHoc, NamHoc, NguoiDung,
                     PhanCongGiangDay, PhuHuynh, TaiKhoan)
from .reports import DichVuBaoCao, ten_cuoi
from .storage import KhoSQLite, kiem_tra_tep_csdl
from .utils import (LoiNghiepVu, bo_dau, chuoi_ngay, doc_ngay, kiem_tra_mat_khau, ma_hoa_mat_khau,
                    ngay_hop_le, xep_loai_hoc_luc)

COT_CSV = ["Mã HS", "Họ tên", "Ngày sinh", "Giới tính", "Nơi sinh", "Dân tộc", "CMND/CCCD", "Địa chỉ",
           "SĐT", "Email", "Lớp", "Trạng thái", "Ngày nhập học"]


class HeThong:
    def __init__(self, duong_dan_db: str = DUONG_DAN_DB, thu_muc_sao_luu: Optional[str] = None,
                 tao_mau: bool = True, tu_dong_sao_luu: bool = True):
        self.duong_dan_db = duong_dan_db
        self.thu_muc_sao_luu = thu_muc_sao_luu or os.path.join(os.path.dirname(duong_dan_db), "sao_luu")
        self.khi_luu = None                       # hàm gọi lại sau mỗi lần lưu (giao diện dùng để cập nhật thanh trạng thái)
        self.lan_luu_cuoi: Optional[datetime] = None
        self.thong_bao_khoi_dong: List[str] = []
        self.tai_khoan_hien_tai: Optional[TaiKhoan] = None
        self._xoa_bo_nho()
        self.kho: Optional[KhoSQLite] = None
        self._mo_kho(tao_mau, tu_dong_sao_luu)

    # ================================================================== khởi tạo / lưu
    def _xoa_bo_nho(self) -> None:
        self.mon_hoc: Dict[str, MonHoc] = {}
        self.nam_hoc: Dict[str, NamHoc] = {}
        self.lop_hoc: Dict[str, LopHoc] = {}
        self.giao_vien: Dict[str, GiaoVien] = {}
        self.hoc_sinh: Dict[str, HocSinh] = {}
        self.phu_huynh: Dict[str, PhuHuynh] = {}
        self.tai_khoan: Dict[str, TaiKhoan] = {}
        self.phan_cong: List[PhanCongGiangDay] = []

    def _thu_doc(self) -> bool:
        self.kho = KhoSQLite(self.duong_dan_db)
        if self.kho.co_du_lieu():
            self.kho.doc(self)
            return True
        return False

    def _mo_kho(self, tao_mau: bool, tu_dong_sao_luu: bool) -> None:
        da_doc = False
        try:
            da_doc = self._thu_doc()
        except (sqlite3.Error, KeyError, ValueError, TypeError) as e:
            # Tệp dữ liệu hỏng: giữ lại bản hỏng để điều tra, rồi thử khôi phục từ bản sao lưu gần nhất.
            if self.kho:
                self.kho.dong()
            hong = f"{self.duong_dan_db}.hong_{datetime.now():%Y%m%d_%H%M%S}"
            shutil.move(self.duong_dan_db, hong)
            self.thong_bao_khoi_dong.append(f"Tệp dữ liệu bị lỗi ({type(e).__name__}); đã giữ lại ở: {hong}")
            self._xoa_bo_nho()
            for b in KhoSQLite.danh_sach_sao_luu(self.thu_muc_sao_luu):
                if not kiem_tra_tep_csdl(b):
                    continue
                shutil.copyfile(b, self.duong_dan_db)
                try:
                    self._xoa_bo_nho()
                    da_doc = self._thu_doc()
                except (sqlite3.Error, KeyError, ValueError, TypeError):
                    self.kho.dong()
                    os.remove(self.duong_dan_db)
                    self._xoa_bo_nho()
                    continue
                if da_doc:
                    self.thong_bao_khoi_dong.append(f"Đã khôi phục dữ liệu từ bản sao lưu: {os.path.basename(b)}")
                    break
            if not da_doc:
                self.kho = KhoSQLite(self.duong_dan_db)
        if da_doc:
            if tu_dong_sao_luu:
                self._sao_luu_tu_dong()
        elif tao_mau:
            from .seed import tao_du_lieu_mau
            tao_du_lieu_mau(self)
            self.luu_du_lieu()
            self.ghi_nhat_ky("Khởi tạo", "Tạo dữ liệu mẫu lần đầu", nguoi="hệ thống")

    def _sao_luu_tu_dong(self) -> None:
        """Mỗi lần mở chương trình, nếu bản sao lưu mới nhất đã quá 6 giờ thì tạo bản mới."""
        ds = KhoSQLite.danh_sach_sao_luu(self.thu_muc_sao_luu)
        if ds and datetime.now().timestamp() - os.path.getmtime(ds[0]) < 6 * 3600:
            return
        try:
            self.kho.sao_luu(self.thu_muc_sao_luu, "tu_dong")
        except (OSError, sqlite3.Error):
            pass

    def luu_du_lieu(self, phan: Optional[Sequence[str]] = None) -> None:
        self.kho.luu(self, phan)
        self.lan_luu_cuoi = datetime.now()
        if self.khi_luu:
            try:
                self.khi_luu()
            except Exception:
                pass

    def dong(self) -> None:
        if self.kho:
            self.kho.dong()

    def ghi_nhat_ky(self, hanh_dong: str, chi_tiet: str = "", nguoi: Optional[str] = None) -> None:
        if nguoi is None:
            nguoi = self.tai_khoan_hien_tai.ten_dang_nhap if self.tai_khoan_hien_tai else "hệ thống"
        self.kho.ghi_nhat_ky(nguoi, hanh_dong, chi_tiet)

    # ================================================================== tra cứu
    def hoc_ky_tat_ca(self) -> List[HocKy]:
        return [hk for n in sorted(self.nam_hoc.values(), key=lambda x: x.ngay_bat_dau) for hk in n.hoc_ky]

    def hoc_ky_hien_tai(self) -> Optional[HocKy]:
        ds, h = self.hoc_ky_tat_ca(), date.today()
        for hk in ds:
            if hk.ngay_bat_dau <= h <= hk.ngay_ket_thuc:
                return hk
        truoc = [hk for hk in ds if hk.ngay_bat_dau <= h]
        return truoc[-1] if truoc else (ds[0] if ds else None)

    def nam_hoc_hien_tai(self) -> Optional[NamHoc]:
        hk = self.hoc_ky_hien_tai()
        return hk.nam_hoc if hk else None

    def nguoi_theo_ma(self, ma: str) -> Optional[NguoiDung]:
        ma = (ma or "").strip().upper()
        return self.hoc_sinh.get(ma) or self.giao_vien.get(ma) or self.phu_huynh.get(ma)

    def ma_tiep_theo(self, tien_to: str, do_dai: int = 3, da_dung=()) -> str:
        i = 1
        while self.nguoi_theo_ma(f"{tien_to}{i:0{do_dai}d}") or f"{tien_to}{i:0{do_dai}d}" in da_dung:
            i += 1
        return f"{tien_to}{i:0{do_dai}d}"

    # ================================================================== đăng nhập
    def dang_nhap(self, ten: str, mat_khau: str) -> TaiKhoan:
        tk = self.tai_khoan.get(ten.strip().lower())
        if tk is None:
            raise LoiNghiepVu("Sai tên đăng nhập hoặc mật khẩu.")
        if not tk.hoat_dong:
            raise LoiNghiepVu("Tài khoản đang bị khóa. Hãy liên hệ quản trị viên.")
        ok = tk.dang_nhap(mat_khau)
        if ok:
            tk.lan_dang_nhap_cuoi = datetime.now().isoformat(sep=" ", timespec="seconds")
        self.luu_du_lieu(["tai_khoan"])                    # lưu số lần sai / trạng thái khóa
        if not ok:
            self.ghi_nhat_ky("Đăng nhập thất bại", tk.ten_dang_nhap, nguoi=tk.ten_dang_nhap)
            raise LoiNghiepVu("Tài khoản đã bị khóa do nhập sai quá nhiều lần." if not tk.hoat_dong
                              else "Sai tên đăng nhập hoặc mật khẩu.")
        self.tai_khoan_hien_tai = tk
        self.ghi_nhat_ky("Đăng nhập")
        return tk

    def dang_xuat(self) -> None:
        if self.tai_khoan_hien_tai:
            self.ghi_nhat_ky("Đăng xuất")
            self.tai_khoan_hien_tai.dang_xuat()
        self.tai_khoan_hien_tai = None

    def mat_khau_mac_dinh_con_dung(self) -> bool:
        tk = self.tai_khoan.get("admin")
        return bool(tk and kiem_tra_mat_khau("admin123", tk.mat_khau_ma_hoa))

    def doi_mat_khau(self, cu: str, moi: str) -> None:
        self.tai_khoan_hien_tai.doi_mat_khau(cu, moi)
        self.luu_du_lieu(["tai_khoan"])
        self.ghi_nhat_ky("Đổi mật khẩu")

    def tao_tai_khoan(self, nguoi: NguoiDung, ten: str, mat_khau: str, vai_tro: VaiTro, luu: bool = True) -> TaiKhoan:
        ten = ten.strip().lower()
        if not ten or ten in self.tai_khoan:
            raise LoiNghiepVu("Tên đăng nhập trống hoặc đã tồn tại.")
        if nguoi.tai_khoan:
            raise LoiNghiepVu("Người này đã có tài khoản (quan hệ 1 – 0..1).")
        if len(mat_khau) < 6:
            raise LoiNghiepVu("Mật khẩu phải có ít nhất 6 ký tự.")
        tk = TaiKhoan(ten, ma_hoa_mat_khau(mat_khau), vai_tro, True, nguoi)
        nguoi.tai_khoan = tk
        self.tai_khoan[ten] = tk
        if luu:
            self.luu_du_lieu(["tai_khoan"])
            self.ghi_nhat_ky("Tạo tài khoản", f"{ten} ({vai_tro.value}) - {nguoi.ma}")
        return tk

    def khoa_mo_tai_khoan(self, tk: TaiKhoan) -> None:
        if tk is self.tai_khoan_hien_tai:
            raise LoiNghiepVu("Không thể tự khóa tài khoản đang đăng nhập.")
        tk.hoat_dong = not tk.hoat_dong
        tk.so_lan_sai = 0
        self.luu_du_lieu(["tai_khoan"])
        self.ghi_nhat_ky("Mở khóa tài khoản" if tk.hoat_dong else "Khóa tài khoản", tk.ten_dang_nhap)

    def dat_lai_mat_khau(self, tk: TaiKhoan, mat_khau: str) -> None:
        tk.dat_mat_khau(mat_khau)
        tk.so_lan_sai = 0
        self.luu_du_lieu(["tai_khoan"])
        self.ghi_nhat_ky("Đặt lại mật khẩu", tk.ten_dang_nhap)

    def xoa_tai_khoan(self, tk: TaiKhoan) -> None:
        if tk is self.tai_khoan_hien_tai:
            raise LoiNghiepVu("Không thể xóa tài khoản đang đăng nhập.")
        if tk.vai_tro is VaiTro.QUAN_TRI and sum(1 for t in self.tai_khoan.values() if t.vai_tro is VaiTro.QUAN_TRI) <= 1:
            raise LoiNghiepVu("Phải còn ít nhất một tài khoản quản trị.")
        tk.chu_so_huu.tai_khoan = None
        del self.tai_khoan[tk.ten_dang_nhap]
        self.luu_du_lieu(["tai_khoan"])
        self.ghi_nhat_ky("Xóa tài khoản", tk.ten_dang_nhap)

    # ================================================================== phân quyền
    def la_quan_tri(self) -> bool:
        return bool(self.tai_khoan_hien_tai and self.tai_khoan_hien_tai.vai_tro is VaiTro.QUAN_TRI)

    def co_quyen_lop(self, lop: Optional[LopHoc]) -> bool:
        tk = self.tai_khoan_hien_tai
        if tk is None:
            return False
        if tk.vai_tro is VaiTro.QUAN_TRI:
            return True
        return tk.vai_tro is VaiTro.GIAO_VIEN and lop is not None and tk.chu_so_huu.duoc_phu_trach(lop)

    def co_quyen_sua(self, hs: HocSinh) -> bool:
        if self.la_quan_tri():
            return True
        return hs.lop_hien_tai is not None and self.co_quyen_lop(hs.lop_hien_tai)

    def ds_lop_duoc_quan_ly(self) -> List[LopHoc]:
        return [l for l in sorted(self.lop_hoc.values(), key=lambda x: x.ma_lop) if self.co_quyen_lop(l)]

    def mon_duoc_nhap_diem(self, lop: LopHoc) -> List[MonHoc]:
        if self.la_quan_tri():
            return sorted(self.mon_hoc.values(), key=lambda m: m.ten_mon)
        gv = self.tai_khoan_hien_tai.chu_so_huu
        return sorted({p.mon_hoc for p in gv.phan_cong if p.lop_hoc is lop and p.ngay_ket_thuc is None},
                      key=lambda m: m.ten_mon)

    # ================================================================== hồ sơ học sinh
    def kiem_tra_ma_trung(self, ma: str) -> bool:
        return self.nguoi_theo_ma(ma) is not None

    def tao_phu_huynh_moi(self, thong_tin: List[dict]) -> List[PhuHuynh]:
        """thong_tin: [{ho_ten, ngay_sinh(date|None), quan_he, nghe, sdt, email, dia_chi}] -> PhuHuynh mới (mã tự sinh)."""
        da_dung, kq = set(), []
        for t in thong_tin:
            if not (t.get("ho_ten") or "").strip():
                continue
            ma = self.ma_tiep_theo("PH", da_dung=da_dung)
            da_dung.add(ma)
            kq.append(PhuHuynh(ma, t["ho_ten"], t.get("ngay_sinh"), self._gioi_tinh_theo_quan_he(t.get("quan_he", "")),
                               t.get("dia_chi", ""), t.get("sdt", ""), t.get("email", ""),
                               t.get("quan_he", ""), t.get("nghe", "")))
        return kq

    @staticmethod
    def _gioi_tinh_theo_quan_he(quan_he: str) -> GioiTinh:
        q = bo_dau(quan_he).lower()
        return GioiTinh.NAM if q in ("bo", "ong", "chu", "bac") else GioiTinh.NU if q in ("me", "ba", "co", "di") \
            else GioiTinh.KHAC

    def them_ho_so_hoc_sinh(self, hs: HocSinh, lop: Optional[LopHoc] = None, phu_huynh=None,
                            tao_tk_hs: bool = False, tao_tk_ph: bool = False) -> List[Tuple[str, str]]:
        """Thêm hồ sơ (include «Kiểm tra mã trùng» + «Lưu dữ liệu»). Trả về các tài khoản đã tạo [(tên, mật khẩu)]."""
        ds_ph = [phu_huynh] if isinstance(phu_huynh, PhuHuynh) else list(phu_huynh or [])
        if self.kiem_tra_ma_trung(hs.ma):
            raise LoiNghiepVu(f"Mã {hs.ma} đã tồn tại.")
        for ph in ds_ph:
            if self.kiem_tra_ma_trung(ph.ma) and ph.ma not in self.phu_huynh:
                raise LoiNghiepVu(f"Mã {ph.ma} đã tồn tại.")
        if tao_tk_hs and hs.ma.lower() in self.tai_khoan:
            raise LoiNghiepVu(f"Tên đăng nhập '{hs.ma.lower()}' đã tồn tại.")
        if lop is not None:
            lop.them_hoc_sinh(hs)                                 # có thể báo lỗi "hết chỗ" trước khi thay đổi gì
        self.hoc_sinh[hs.ma] = hs
        for ph in ds_ph:
            ph = self.phu_huynh.setdefault(ph.ma, ph)
            hs.them_phu_huynh(ph)
        tk_moi = []
        if tao_tk_hs:
            self.tao_tai_khoan(hs, hs.ma.lower(), MAT_KHAU_MAC_DINH, VaiTro.HOC_SINH, luu=False)
            tk_moi.append((hs.ma.lower(), MAT_KHAU_MAC_DINH))
        if tao_tk_ph:
            for ph in hs.phu_huynh[:1]:
                if not ph.tai_khoan and ph.ma.lower() not in self.tai_khoan:
                    self.tao_tai_khoan(ph, ph.ma.lower(), MAT_KHAU_MAC_DINH, VaiTro.PHU_HUYNH, luu=False)
                    tk_moi.append((ph.ma.lower(), MAT_KHAU_MAC_DINH))
        self.luu_du_lieu(["nguoi", "tai_khoan"])
        self.ghi_nhat_ky("Thêm hồ sơ học sinh", f"{hs.ma} - {hs.ho_ten}" + (f" (lớp {lop.ten_lop})" if lop else ""))
        return tk_moi

    def sua_ho_so_hoc_sinh(self, hs: HocSinh, moi: HocSinh, lop: Optional[LopHoc], trang_thai: TrangThaiHocSinh,
                           suc_khoe: str, thanh_tich: str, ky_luat: str, ngay_nhap_hoc: Optional[date] = None) -> None:
        """`moi`: HocSinh tạm đã qua kiểm tra hợp lệ trong constructor, dùng để chép thông tin sang `hs`."""
        if trang_thai is not TrangThaiHocSinh.DANG_HOC and lop is not None and lop is not hs.lop_hien_tai:
            raise LoiNghiepVu("Chỉ học sinh 'Đang học' mới được xếp vào lớp.")
        if trang_thai is TrangThaiHocSinh.DANG_HOC:
            if lop is not None and lop is not hs.lop_hien_tai:
                hs.chuyen_lop(lop) if hs.lop_hien_tai else hs.nhap_hoc(lop)
        elif hs.lop_hien_tai is not None:                       # bảo lưu / chuyển trường / tốt nghiệp -> rời lớp
            hs.lop_hien_tai.xoa_hoc_sinh(hs)
        for a in ("ho_ten", "ngay_sinh", "gioi_tinh", "dia_chi", "so_dien_thoai", "email", "noi_sinh", "dan_toc", "so_cccd"):
            setattr(hs, a, getattr(moi, a))
        hs.trang_thai = trang_thai
        if ngay_nhap_hoc:
            hs.ngay_nhap_hoc = ngay_nhap_hoc
        hs.ho_so.cap_nhat_ho_so(suc_khoe, thanh_tich, ky_luat)
        self.luu_du_lieu(["nguoi"])
        self.ghi_nhat_ky("Sửa hồ sơ học sinh", f"{hs.ma} - {hs.ho_ten}")

    def cap_nhat_phu_huynh_cua_hs(self, hs: HocSinh, thong_tin: List[dict], tao_tk: bool = False) -> None:
        """Cập nhật tối đa 2 phụ huynh đầu tiên của học sinh; ô họ tên trống = bỏ qua."""
        for i, t in enumerate(thong_tin):
            if not (t.get("ho_ten") or "").strip():
                continue
            if i < len(hs.phu_huynh):
                ph = hs.phu_huynh[i]
                tam = PhuHuynh(ph.ma, t["ho_ten"], t.get("ngay_sinh"), ph.gioi_tinh, t.get("dia_chi", ph.dia_chi),
                               t.get("sdt", ""), t.get("email", ""), t.get("quan_he", ""), t.get("nghe", ""))
                for a in ("ho_ten", "ngay_sinh", "dia_chi", "so_dien_thoai", "email", "quan_he", "nghe_nghiep"):
                    setattr(ph, a, getattr(tam, a))
            else:
                ph = self.tao_phu_huynh_moi([t])[0]
                self.phu_huynh[ph.ma] = ph
                hs.them_phu_huynh(ph)
            if tao_tk and i == 0 and not ph.tai_khoan and ph.ma.lower() not in self.tai_khoan:
                self.tao_tai_khoan(ph, ph.ma.lower(), MAT_KHAU_MAC_DINH, VaiTro.PHU_HUYNH, luu=False)
        self.luu_du_lieu(["nguoi", "tai_khoan"])

    def chuyen_lop(self, hs: HocSinh, lop_moi: LopHoc) -> None:
        cu = hs.lop_hien_tai
        if hs.trang_thai is not TrangThaiHocSinh.DANG_HOC:
            raise LoiNghiepVu("Chỉ chuyển lớp cho học sinh đang học.")
        hs.chuyen_lop(lop_moi) if cu else hs.nhap_hoc(lop_moi)
        self.luu_du_lieu(["nguoi"])
        self.ghi_nhat_ky("Chuyển lớp", f"{hs.ma} - {hs.ho_ten}: {cu.ten_lop if cu else '(chưa có)'} → {lop_moi.ten_lop}")

    def tim_ho_so_theo_ma(self, ma: str) -> Optional[HocSinh]:
        return self.hoc_sinh.get(ma.strip().upper())

    def tim_kiem(self, tu_khoa: str) -> List[HocSinh]:
        k = bo_dau(tu_khoa).lower().strip()
        return [h for h in self.hoc_sinh.values()
                if k in h.ma.lower() or k in bo_dau(h.ho_ten).lower() or (k and k in h.so_dien_thoai)]

    def danh_sach(self, sap_xep: str = "ma") -> List[HocSinh]:
        ds = list(self.hoc_sinh.values())
        khoa = {"ma": lambda h: h.ma,
                "ten": lambda h: (ten_cuoi(h.ho_ten), bo_dau(h.ho_ten).lower()),
                "ngaysinh": lambda h: h.ngay_sinh or date.min,
                "lop": lambda h: (h.lop_hien_tai.ma_lop if h.lop_hien_tai else "~", h.ma)}
        return sorted(ds, key=khoa.get(sap_xep, khoa["ma"]))

    def xoa_ho_so(self, hs: HocSinh) -> None:
        if hs.diem or hs.diem_danh or hs.ket_qua_hanh_kiem:
            raise LoiNghiepVu("Hồ sơ đã có dữ liệu điểm/điểm danh/hạnh kiểm nên không thể xóa. "
                              "Hãy đổi trạng thái (Bảo lưu / Chuyển trường / Đã tốt nghiệp).")
        for g in hs.ghi_danh:
            g.lop_hoc.ghi_danh.remove(g)
        for ph in list(hs.phu_huynh):
            ph.hoc_sinh.remove(hs)
            if not ph.hoc_sinh:                            # phụ huynh không còn con nào -> xóa luôn
                if ph.tai_khoan:
                    self.tai_khoan.pop(ph.tai_khoan.ten_dang_nhap, None)
                self.phu_huynh.pop(ph.ma, None)
        if hs.tai_khoan:
            self.tai_khoan.pop(hs.tai_khoan.ten_dang_nhap, None)
        del self.hoc_sinh[hs.ma]
        self.luu_du_lieu(["nguoi", "tai_khoan"])
        self.ghi_nhat_ky("Xóa hồ sơ học sinh", f"{hs.ma} - {hs.ho_ten}")

    # ---------- CSV ----------
    def xuat_csv(self, duong_dan: str, ds: Optional[List[HocSinh]] = None) -> str:
        from .exporters import ghi_csv
        ds = self.danh_sach() if ds is None else ds
        ghi_csv(duong_dan, COT_CSV, [[h.ma_hoc_sinh, h.ho_ten, chuoi_ngay(h.ngay_sinh), h.gioi_tinh.value, h.noi_sinh,
                                      h.dan_toc, h.so_cccd, h.dia_chi, h.so_dien_thoai, h.email,
                                      h.lop_hien_tai.ten_lop if h.lop_hien_tai else "", h.trang_thai.value,
                                      chuoi_ngay(h.ngay_nhap_hoc)] for h in ds])
        return duong_dan

    def xuat_csv_mau(self, duong_dan: str) -> str:
        from .exporters import ghi_csv
        ghi_csv(duong_dan, COT_CSV, [
            ["HS900", "Nguyễn Văn Mẫu", "01/02/2010", "Nam", "Hải Phòng", "Kinh", "", "12 Lạch Tray, Hải Phòng",
             "0901234567", "", "10A1", "Đang học", "05/09/2026"],
            ["HS901", "Trần Thị Mẫu", "03/04/2010", "Nữ", "Hải Phòng", "Kinh", "", "", "", "", "", "Đang học", ""]])
        return duong_dan

    def nhap_csv(self, duong_dan: str) -> Tuple[int, List[str]]:
        """Nhập học sinh từ CSV. Trả về (số dòng thành công, danh sách lỗi theo dòng)."""
        ok, loi = 0, []
        with open(duong_dan, encoding="utf-8-sig", newline="") as f:
            rd = csv.DictReader(f)
            thieu = [c for c in ("Mã HS", "Họ tên", "Ngày sinh") if c not in (rd.fieldnames or [])]
            if thieu:
                raise LoiNghiepVu("Tệp CSV thiếu cột bắt buộc: " + ", ".join(thieu))
            for so_dong, r in enumerate(rd, start=2):
                lay = lambda k: (r.get(k) or "").strip()
                try:
                    ma = lay("Mã HS").upper()
                    if self.kiem_tra_ma_trung(ma):
                        raise LoiNghiepVu(f"Mã {ma} đã tồn tại.")
                    gt = {"nam": GioiTinh.NAM, "nữ": GioiTinh.NU, "nu": GioiTinh.NU}.get(lay("Giới tính").lower(), GioiTinh.KHAC)
                    tt = next((t for t in TrangThaiHocSinh if t.value.lower() == lay("Trạng thái").lower()),
                              TrangThaiHocSinh.DANG_HOC)
                    try:
                        ns = ngay_hop_le(lay("Ngày sinh"), "Ngày sinh")
                    except LoiNghiepVu:
                        ns = date.fromisoformat(lay("Ngày sinh"))
                    hs = HocSinh(ma, lay("Họ tên"), ns, gt, lay("Địa chỉ"), lay("SĐT"), lay("Email"),
                                 ngay_hop_le(lay("Ngày nhập học"), "Ngày nhập học", False), tt,
                                 lay("Nơi sinh"), lay("Dân tộc") or "Kinh", lay("CMND/CCCD"))
                    lop = None
                    if lay("Lớp"):
                        lop = self.lop_hoc.get(lay("Lớp").upper()) or next(
                            (l for l in self.lop_hoc.values() if l.ten_lop.lower() == lay("Lớp").lower()), None)
                        if lop is None:
                            raise LoiNghiepVu(f"Không có lớp '{lay('Lớp')}'.")
                        if tt is not TrangThaiHocSinh.DANG_HOC:
                            lop = None
                    if lop is not None:
                        lop.them_hoc_sinh(hs)
                    self.hoc_sinh[hs.ma] = hs
                    ok += 1
                except (LoiNghiepVu, ValueError) as e:
                    loi.append(f"Dòng {so_dong}: {e}")
        if ok:
            self.luu_du_lieu(["nguoi"])
            self.ghi_nhat_ky("Nhập CSV", f"{ok} học sinh, {len(loi)} dòng lỗi")
        return ok, loi

    # ================================================================== điểm / hạnh kiểm / điểm danh
    def luu_bang_diem_lop(self, lop: LopHoc, mon: MonHoc, hk: HocKy, du_lieu: Dict[str, dict]) -> int:
        """du_lieu[ma_hs] = {'tx': [điểm...], 'gk': float|None, 'ck': float|None}"""
        if mon not in self.mon_duoc_nhap_diem(lop):
            raise LoiNghiepVu("Bạn chưa được phân công dạy môn này ở lớp này.")
        gv = self.tai_khoan_hien_tai.chu_so_huu
        trong_lop = {h.ma for h in lop.danh_sach_hoc_sinh()}
        for ma, d in du_lieu.items():
            if ma in trong_lop:
                gv.luu_bang_diem(self.hoc_sinh[ma], mon, hk, d["tx"], d["gk"], d["ck"])
        self.luu_du_lieu(["diem"])
        self.ghi_nhat_ky("Nhập điểm", f"Lớp {lop.ten_lop} - {mon.ten_mon} - {hk}")
        return len(du_lieu)

    def luu_hanh_kiem_lop(self, lop: LopHoc, hk: HocKy, du_lieu: Dict[str, Tuple[Optional[XepLoaiHanhKiem], str]]) -> None:
        gv = self.tai_khoan_hien_tai.chu_so_huu
        if not (self.la_quan_tri() or lop.giao_vien_chu_nhiem is gv):
            raise LoiNghiepVu("Chỉ giáo viên chủ nhiệm (hoặc quản trị viên) được xếp loại hạnh kiểm.")
        for ma, (xl, nx) in du_lieu.items():
            hs = self.hoc_sinh[ma]
            hs.ket_qua_hanh_kiem = [k for k in hs.ket_qua_hanh_kiem if k.hoc_ky is not hk]
            if xl is not None:
                hs.ket_qua_hanh_kiem.append(KetQuaHanhKiem(hs, hk, xl, nx.strip()))
        self.luu_du_lieu(["hanh_kiem"])
        self.ghi_nhat_ky("Xếp loại hạnh kiểm", f"Lớp {lop.ten_lop} - {hk}")

    def luu_diem_danh(self, lop: LopHoc, ngay: date, tt: Dict[str, TrangThaiDiemDanh], gc: Dict[str, str]) -> None:
        if not self.co_quyen_lop(lop):
            raise LoiNghiepVu("Bạn không phụ trách lớp này.")
        if ngay > date.today():
            raise LoiNghiepVu("Không thể điểm danh cho ngày trong tương lai.")
        self.tai_khoan_hien_tai.chu_so_huu.diem_danh(lop, ngay, tt, gc)
        self.luu_du_lieu(["diem_danh"])
        self.ghi_nhat_ky("Điểm danh", f"Lớp {lop.ten_lop} - {chuoi_ngay(ngay)}")

    # ================================================================== tổng quan
    def tong_quan(self, lops: Optional[List[LopHoc]] = None) -> dict:
        lops = list(self.lop_hoc.values()) if lops is None else lops
        ds_hs = [h for l in sorted(lops, key=lambda x: x.ma_lop) for h in l.danh_sach_hoc_sinh()]
        hk = self.hoc_ky_hien_tai()
        dtb = [d for d in (h.tinh_diem_trung_binh(hk) for h in ds_hs) if d] if hk else []
        moc = date.today() - timedelta(days=30)
        can_chu_y = []
        for h in ds_hs:
            ly_do = []
            d = h.tinh_diem_trung_binh(hk) if hk else 0
            if d and d < 5.0:
                ly_do.append(f"ĐTB thấp ({d:.2f})")
            vkp = h.thong_ke_diem_danh(moc)[TrangThaiDiemDanh.VANG_KHONG_PHEP]
            if vkp >= 2:
                ly_do.append(f"Vắng không phép {vkp} buổi/30 ngày")
            if ly_do:
                can_chu_y.append((h, "; ".join(ly_do)))
        return {
            "hoc_ky": hk,
            "so_hs_dang_hoc": len(ds_hs),
            "so_hs_tong": len(self.hoc_sinh),
            "so_gv": len(self.giao_vien),
            "so_lop": len(lops),
            "dtb_truong": sum(dtb) / len(dtb) if dtb else None,
            "chuyen_can": DichVuBaoCao.ty_le_chuyen_can(ds_hs, moc),
            "phan_bo_hoc_luc": DichVuBaoCao.phan_bo_hoc_luc(ds_hs, hk),
            "si_so": [(l.ten_lop, l.dem_si_so(), l.si_so_toi_da) for l in sorted(lops, key=lambda x: x.ma_lop)],
            "gioi_tinh": {g.value: sum(1 for h in ds_hs if h.gioi_tinh is g) for g in GioiTinh},
            "trang_thai": {t.value: sum(1 for h in self.hoc_sinh.values() if h.trang_thai is t) for t in TrangThaiHocSinh},
            "can_chu_y": sorted(can_chu_y, key=lambda x: x[0].ma)[:100],
        }

    # ================================================================== quản trị: lớp / môn / giáo viên / năm học
    def them_lop(self, ma: str, ten: str, khoi: int, si_so: int, nam: str, gvcn: Optional[GiaoVien]) -> LopHoc:
        ma = ma.strip().upper()
        if not ma or not ten.strip():
            raise LoiNghiepVu("Mã lớp và tên lớp không được để trống.")
        if ma in self.lop_hoc:
            raise LoiNghiepVu("Mã lớp đã tồn tại.")
        lop = LopHoc(ma, ten.strip(), khoi, si_so)
        lop.nam_hoc = self.nam_hoc.get(nam)
        if lop.nam_hoc:
            lop.nam_hoc.lop_hoc.append(lop)
        self.lop_hoc[ma] = lop
        self._dat_gvcn(lop, gvcn)
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Thêm lớp", f"{lop.ma_lop} - {lop.ten_lop}")
        return lop

    def sua_lop(self, lop: LopHoc, ten: str, si_so: int, gvcn: Optional[GiaoVien]) -> None:
        if not ten.strip():
            raise LoiNghiepVu("Tên lớp không được để trống.")
        if si_so < lop.dem_si_so():
            raise LoiNghiepVu(f"Lớp đang có {lop.dem_si_so()} học sinh, không thể đặt sĩ số tối đa nhỏ hơn.")
        lop.ten_lop, lop.si_so_toi_da = ten.strip(), si_so
        self._dat_gvcn(lop, gvcn)
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Sửa lớp", f"{lop.ma_lop} - {lop.ten_lop}")

    @staticmethod
    def _dat_gvcn(lop: LopHoc, gv: Optional[GiaoVien]) -> None:
        if lop.giao_vien_chu_nhiem is not gv:
            if lop.giao_vien_chu_nhiem:
                lop.giao_vien_chu_nhiem.lop_chu_nhiem.remove(lop)
            lop.giao_vien_chu_nhiem = gv
            if gv:
                gv.lop_chu_nhiem.append(lop)

    def xoa_lop(self, lop: LopHoc) -> None:
        if lop.ghi_danh:
            raise LoiNghiepVu("Lớp đã có học sinh hoặc lịch sử ghi danh nên không thể xóa.")
        if lop.nam_hoc:
            lop.nam_hoc.lop_hoc.remove(lop)
        self._dat_gvcn(lop, None)
        for x in list(lop.phan_cong):
            x.giao_vien.phan_cong.remove(x)
            self.phan_cong.remove(x)
        del self.lop_hoc[lop.ma_lop]
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Xóa lớp", lop.ma_lop)

    def them_phan_cong(self, gv: GiaoVien, lop: LopHoc, mon: MonHoc) -> None:
        if any(x.mon_hoc is mon and x.ngay_ket_thuc is None for x in lop.phan_cong):
            raise LoiNghiepVu(f"Môn {mon.ten_mon} ở lớp {lop.ten_lop} đã có giáo viên phụ trách "
                              f"({lop.giao_vien_day(mon).ho_ten}). Hãy kết thúc phân công cũ trước.")
        pc = PhanCongGiangDay(gv, lop, mon, date.today())
        self.phan_cong.append(pc)
        gv.phan_cong.append(pc)
        lop.phan_cong.append(pc)
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Phân công giảng dạy", f"{gv.ma} - {lop.ten_lop} - {mon.ten_mon}")

    def ket_thuc_phan_cong(self, lop: LopHoc, mon: MonHoc) -> None:
        pc = next((x for x in lop.phan_cong if x.mon_hoc is mon and x.ngay_ket_thuc is None), None)
        if pc is None:
            raise LoiNghiepVu("Không có phân công đang hiệu lực.")
        pc.ngay_ket_thuc = date.today()
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Kết thúc phân công", f"{pc.giao_vien.ma} - {lop.ten_lop} - {mon.ten_mon}")

    def them_mon(self, ma: str, ten: str, tin_chi: int, he_so: int) -> MonHoc:
        ma = ma.strip().upper()
        if not ma or not ten.strip():
            raise LoiNghiepVu("Mã môn và tên môn không được để trống.")
        if ma in self.mon_hoc:
            raise LoiNghiepVu("Mã môn đã tồn tại.")
        m = self.mon_hoc[ma] = MonHoc(ma, ten.strip(), tin_chi, he_so)
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Thêm môn học", f"{ma} - {ten}")
        return m

    def sua_mon(self, mon: MonHoc, ten: str, tin_chi: int, he_so: int) -> None:
        if not ten.strip():
            raise LoiNghiepVu("Tên môn không được để trống.")
        mon.ten_mon, mon.so_tin_chi, mon.he_so = ten.strip(), tin_chi, he_so
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Sửa môn học", mon.ma_mon)

    def xoa_mon(self, mon: MonHoc) -> None:
        if any(d.mon_hoc is mon for h in self.hoc_sinh.values() for d in h.diem) or \
                any(p.mon_hoc is mon for p in self.phan_cong):
            raise LoiNghiepVu("Môn đã có điểm hoặc đã được phân công giảng dạy nên không thể xóa.")
        del self.mon_hoc[mon.ma_mon]
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Xóa môn học", mon.ma_mon)

    def them_giao_vien(self, gv: GiaoVien) -> None:
        if self.kiem_tra_ma_trung(gv.ma):
            raise LoiNghiepVu("Mã đã tồn tại.")
        self.giao_vien[gv.ma] = gv
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Thêm giáo viên", f"{gv.ma} - {gv.ho_ten}")

    def sua_giao_vien(self, gv: GiaoVien, moi: GiaoVien) -> None:
        for a in ("ho_ten", "ngay_sinh", "gioi_tinh", "dia_chi", "so_dien_thoai", "email", "chuyen_mon", "trinh_do"):
            setattr(gv, a, getattr(moi, a))
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Sửa giáo viên", f"{gv.ma} - {gv.ho_ten}")

    def xoa_giao_vien(self, gv: GiaoVien) -> None:
        if gv.lop_chu_nhiem or any(p.ngay_ket_thuc is None for p in gv.phan_cong):
            raise LoiNghiepVu("Giáo viên đang chủ nhiệm/được phân công. Hãy gỡ trước.")
        if gv.phan_cong:
            raise LoiNghiepVu("Giáo viên đã có lịch sử giảng dạy nên không thể xóa.")
        if gv.tai_khoan is self.tai_khoan_hien_tai:
            raise LoiNghiepVu("Không thể xóa chính tài khoản đang đăng nhập.")
        if gv.tai_khoan:
            self.tai_khoan.pop(gv.tai_khoan.ten_dang_nhap, None)
        del self.giao_vien[gv.ma]
        self.luu_du_lieu(["danh_muc", "tai_khoan"])
        self.ghi_nhat_ky("Xóa giáo viên", f"{gv.ma} - {gv.ho_ten}")

    def them_nam_hoc(self, ten: str, bat_dau: date, ket_thuc: date, ngay_chia_hk: date) -> NamHoc:
        ten = ten.strip()
        if not ten or ten in self.nam_hoc:
            raise LoiNghiepVu("Tên năm học trống hoặc đã tồn tại.")
        if not bat_dau < ngay_chia_hk < ket_thuc:
            raise LoiNghiepVu("Cần có: ngày bắt đầu < ngày kết thúc học kỳ 1 < ngày kết thúc năm học.")
        nh = NamHoc(ten, bat_dau, ket_thuc)
        nh.them_hoc_ky(HocKy("Học kỳ 1", bat_dau, ngay_chia_hk))
        nh.them_hoc_ky(HocKy("Học kỳ 2", ngay_chia_hk + timedelta(days=1), ket_thuc))
        self.nam_hoc[ten] = nh
        self.luu_du_lieu(["danh_muc"])
        self.ghi_nhat_ky("Thêm năm học", ten)
        return nh

    # ================================================================== hệ thống: sao lưu / khôi phục / thông tin
    def sao_luu_ngay(self) -> str:
        p = self.kho.sao_luu(self.thu_muc_sao_luu, "thu_cong")
        self.ghi_nhat_ky("Sao lưu dữ liệu", os.path.basename(p))
        return p

    def danh_sach_sao_luu(self) -> List[str]:
        return KhoSQLite.danh_sach_sao_luu(self.thu_muc_sao_luu)

    def phuc_hoi(self, tep: str) -> None:
        """Khôi phục dữ liệu từ bản sao lưu. Tự sao lưu trạng thái hiện tại trước. Người dùng phải đăng nhập lại."""
        if not kiem_tra_tep_csdl(tep):
            raise LoiNghiepVu("Đây không phải là tệp sao lưu hợp lệ của chương trình.")
        self.kho.sao_luu(self.thu_muc_sao_luu, "truoc_khi_phuc_hoi")
        self.kho.dong()
        shutil.copyfile(tep, self.duong_dan_db)
        self._xoa_bo_nho()
        self.kho = KhoSQLite(self.duong_dan_db)
        self.kho.doc(self)
        self.tai_khoan_hien_tai = None
        self.ghi_nhat_ky("Khôi phục dữ liệu", os.path.basename(tep), nguoi="hệ thống")

    def nhap_du_lieu_cu(self, duong_dan: str) -> str:
        from .legacy import nhap_json_cu
        kq = nhap_json_cu(self, duong_dan)
        self.ghi_nhat_ky("Nhập dữ liệu từ phiên bản cũ", kq)
        return kq

    def thong_tin_he_thong(self) -> dict:
        return {"tep_du_lieu": self.duong_dan_db, "dung_luong": self.kho.dung_luong(),
                "thu_muc_sao_luu": self.thu_muc_sao_luu, "so_ban_sao_luu": len(self.danh_sach_sao_luu()),
                "so_hs": len(self.hoc_sinh), "so_gv": len(self.giao_vien), "so_ph": len(self.phu_huynh),
                "so_lop": len(self.lop_hoc), "so_mon": len(self.mon_hoc), "so_tai_khoan": len(self.tai_khoan),
                "so_diem": sum(len(h.diem) for h in self.hoc_sinh.values()),
                "so_diem_danh": sum(len(h.diem_danh) for h in self.hoc_sinh.values()),
                "lan_luu_cuoi": self.lan_luu_cuoi}
