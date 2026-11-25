# -*- coding: utf-8 -*-
"""Dữ liệu mẫu quy mô "trường thật": 9 lớp (khối 10-12), ~330 học sinh, 24 giáo viên, 12 môn,
phân công giảng dạy, điểm, điểm danh, hạnh kiểm, phụ huynh và tài khoản đăng nhập.

Tài khoản mẫu:  admin/admin123 · gv01/gv123 · hs001/hs123 · ph001/ph123   (và gvNN, hsNNN, phNNN tương tự)
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import List

from .enums import GioiTinh, TrangThaiDiemDanh, TrangThaiHocSinh, VaiTro, XepLoaiHanhKiem
from .models import (Diem, DiemDanh, GiaoVien, HocKy, HocSinh, KetQuaHanhKiem, LopHoc, MonHoc, NamHoc,
                     PhanCongGiangDay, PhuHuynh, TaiKhoan)
from .enums import LoaiDiem
from .utils import bo_dau, ma_hoa_mat_khau

HO = ["Nguyễn"] * 6 + ["Trần"] * 3 + ["Lê"] * 2 + ["Phạm"] * 2 + ["Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi",
                                                                   "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đinh", "Đoàn", "Lương", "Mai"]
DEM_NAM = ["Văn", "Minh", "Quang", "Đức", "Hữu", "Gia", "Thành", "Công", "Anh", "Tuấn", "Bảo", "Quốc", "Hải", "Đình"]
TEN_NAM = ["An", "Bình", "Cường", "Dũng", "Đạt", "Hải", "Hiếu", "Hoàng", "Hùng", "Khang", "Khánh", "Kiên", "Long",
           "Nam", "Phúc", "Quân", "Sơn", "Thắng", "Thịnh", "Trung", "Tuấn", "Việt", "Vinh", "Huy", "Lâm", "Nghĩa",
           "Phong", "Tài", "Toàn", "Đức", "Duy", "Hưng", "Khôi", "Minh", "Nhân", "Thái", "Tiến", "Trí"]
DEM_NU = ["Thị", "Ngọc", "Thu", "Thùy", "Phương", "Mai", "Khánh", "Bảo", "Hồng", "Diệu", "Kim", "Minh", "Thanh", "Hoài"]
TEN_NU = ["An", "Anh", "Bích", "Chi", "Dung", "Giang", "Hà", "Hạnh", "Hằng", "Hoa", "Hương", "Lan", "Linh", "Ly", "Mai",
          "My", "Ngân", "Ngọc", "Nhi", "Oanh", "Phương", "Quỳnh", "Thảo", "Thu", "Trang", "Trinh", "Vân", "Yến", "Thủy",
          "Huyền", "Châu", "Diệp", "Hiền", "Khánh", "Loan", "Nga", "Thư", "Uyên"]
QUAN = ["Hồng Bàng", "Ngô Quyền", "Lê Chân", "Kiến An", "Hải An", "Đồ Sơn", "Dương Kinh", "Thủy Nguyên", "An Dương",
        "An Lão", "Kiến Thụy", "Tiên Lãng", "Vĩnh Bảo", "Cát Hải"]
DUONG = ["Lạch Tray", "Điện Biên Phủ", "Trần Nguyên Hãn", "Lê Lợi", "Cầu Đất", "Nguyễn Đức Cảnh", "Tô Hiệu", "Văn Cao",
         "Máy Chai", "Hoàng Quốc Việt", "Phạm Văn Đồng", "Nguyễn Bỉnh Khiêm", "Trường Chinh", "Đà Nẵng", "Tôn Đức Thắng"]
NGHE = ["Kỹ sư", "Giáo viên", "Bác sĩ", "Công nhân", "Kinh doanh", "Nhân viên văn phòng", "Lái xe", "Nông dân",
        "Công chức", "Thợ cơ khí", "Dược sĩ", "Kế toán", "Buôn bán tự do", "Thuyền viên", "Kiến trúc sư"]
NOI_SINH = ["Hải Phòng"] * 8 + ["Hải Dương", "Thái Bình", "Quảng Ninh", "Hà Nội"]
SUC_KHOE = [""] * 10 + ["Cận thị nhẹ", "Dị ứng hải sản", "Hen suyễn nhẹ", "Sức khỏe tốt", "Đeo kính cận", "Thiếu máu nhẹ"]
THANH_TICH = [""] * 10 + ["Học sinh giỏi cấp trường", "Giải Ba Olympic Toán cấp thành phố", "Giải Nhì cờ vua học sinh",
                          "Đạt chứng chỉ IELTS 6.5", "Cán bộ lớp xuất sắc", "Giải Khuyến khích HSG Tiếng Anh",
                          "Đội tuyển bóng đá của trường"]

MON = [("TOAN", "Toán", 3, 2), ("VAN", "Ngữ văn", 3, 2), ("ANH", "Tiếng Anh", 2, 1), ("LY", "Vật lí", 2, 1),
       ("HOA", "Hóa học", 2, 1), ("SINH", "Sinh học", 2, 1), ("SU", "Lịch sử", 2, 1), ("DIA", "Địa lí", 2, 1),
       ("GDCD", "GDCD", 1, 1), ("TIN", "Tin học", 1, 1), ("THEDUC", "Thể dục", 1, 1), ("CNGHE", "Công nghệ", 1, 1)]
LOP = [("10A1", 10), ("10A2", 10), ("10A3", 10), ("11A1", 11), ("11A2", 11), ("11A3", 11),
       ("12A1", 12), ("12A2", 12), ("12A3", 12)]


def _ten(rnd, nu: bool, ho=None) -> str:
    ho = ho or rnd.choice(HO)
    return f"{ho} {rnd.choice(DEM_NU if nu else DEM_NAM)} {rnd.choice(TEN_NU if nu else TEN_NAM)}"


def _sdt(rnd) -> str:
    return rnd.choice(["090", "091", "093", "094", "096", "097", "098", "086", "035", "070"]) + "".join(
        str(rnd.randint(0, 9)) for _ in range(7))


def _dia_chi(rnd) -> str:
    return f"Số {rnd.randint(1, 250)} đường {rnd.choice(DUONG)}, quận {rnd.choice(QUAN)}, Hải Phòng"


def _tai_khoan(ht, nguoi, ten, mat_khau, vai_tro, so_lan=1000) -> None:
    tk = TaiKhoan(ten, ma_hoa_mat_khau(mat_khau, so_lan=so_lan), vai_tro, True, nguoi)
    nguoi.tai_khoan = tk
    ht.tai_khoan[ten] = tk


def _ngay_ngau_nhien(rnd, nam: int) -> date:
    return date(nam, 1, 1) + timedelta(days=rnd.randint(0, 364))


def _buoc(x: float, b: float) -> float:
    return round(min(10.0, max(0.0, x)) / b) * b


def tao_du_lieu_mau(ht) -> None:
    rnd = random.Random(20261123)
    hom_nay = date.today()
    nam = hom_nay.year if hom_nay.month >= 8 else hom_nay.year - 1
    bat_dau = date(nam, 9, 5)

    # ---------------- năm học, học kỳ, môn học ----------------
    nh = NamHoc(f"{nam}-{nam + 1}", bat_dau, date(nam + 1, 5, 31))
    nh.them_hoc_ky(HocKy("Học kỳ 1", bat_dau, date(nam + 1, 1, 15)))
    nh.them_hoc_ky(HocKy("Học kỳ 2", date(nam + 1, 1, 16), date(nam + 1, 5, 31)))
    ht.nam_hoc[nh.ten_nam_hoc] = nh
    for ma, ten, tc, hs in MON:
        ht.mon_hoc[ma] = MonHoc(ma, ten, tc, hs)

    # ---------------- giáo viên (2 người / môn) ----------------
    qt = GiaoVien("GV00", "Quản trị hệ thống", date(1985, 1, 1), GioiTinh.NAM, "Hải Phòng", chuyen_mon="Quản trị",
                  trinh_do="Kỹ sư CNTT")
    ht.giao_vien[qt.ma] = qt
    _tai_khoan(ht, qt, "admin", "admin123", VaiTro.QUAN_TRI, so_lan=150_000)
    gv_theo_mon: dict = {}
    for i in range(1, 25):
        ma_mon = MON[(i - 1) // 2][0]
        if i == 1:
            gv = GiaoVien("GV01", "Phạm Thị Thịnh", date(1988, 4, 12), GioiTinh.NU, "Hải Phòng", "0912345678",
                          "gv01@truong.edu.vn", "Toán", "Thạc sĩ")
        else:
            nu = rnd.random() < 0.65
            ten = _ten(rnd, nu)
            gv = GiaoVien(f"GV{i:02d}", ten, _ngay_ngau_nhien(rnd, rnd.randint(1972, 1996)),
                          GioiTinh.NU if nu else GioiTinh.NAM, _dia_chi(rnd), _sdt(rnd),
                          f"gv{i:02d}@truong.edu.vn", ht.mon_hoc[ma_mon].ten_mon,
                          rnd.choice(["Cử nhân", "Cử nhân", "Thạc sĩ", "Thạc sĩ", "Tiến sĩ"]))
        ht.giao_vien[gv.ma] = gv
        gv_theo_mon.setdefault(ma_mon, []).append(gv)
        _tai_khoan(ht, gv, gv.ma.lower(), "gv123", VaiTro.GIAO_VIEN)

    # ---------------- lớp học + phân công ----------------
    lops: List[LopHoc] = []
    for idx, (ma, khoi) in enumerate(LOP):
        lop = LopHoc(ma, ma, khoi, 40)
        lop.nam_hoc = nh
        nh.lop_hoc.append(lop)
        ht.lop_hoc[ma] = lop
        lops.append(lop)
        for ma_mon, (g1, g2) in gv_theo_mon.items():
            gv = g1 if idx <= 4 else g2
            pc = PhanCongGiangDay(gv, lop, ht.mon_hoc[ma_mon], bat_dau)
            ht.phan_cong.append(pc)
            gv.phan_cong.append(pc)
            lop.phan_cong.append(pc)
        gvcn = (gv_theo_mon[MON[idx][0]][0] if idx <= 4 else gv_theo_mon[MON[idx][0]][1])
        lop.giao_vien_chu_nhiem = gvcn
        gvcn.lop_chu_nhiem.append(lop)

    # ---------------- học sinh + phụ huynh ----------------
    dem_hs = [0]
    dem_ph = [0]
    nang_luc = {}

    def tao_phu_huynh(ho_hs: str, dia_chi: str, dau: bool = False) -> List[PhuHuynh]:
        kq = []
        for quan_he, nu in (("Bố", False), ("Mẹ", True)):
            if quan_he == "Mẹ" and rnd.random() < 0.08:
                continue
            dem_ph[0] += 1
            ma = f"PH{dem_ph[0]:03d}"
            if dau and quan_he == "Bố":
                ph = PhuHuynh(ma, "Nguyễn Văn Bình", date(1975, 6, 1), GioiTinh.NAM, "Hải Phòng", "0987654321",
                              quan_he="Bố", nghe_nghiep="Kỹ sư")
            else:
                ten = _ten(rnd, nu, ho_hs if not nu else None)
                ph = PhuHuynh(ma, ten, _ngay_ngau_nhien(rnd, rnd.randint(1962, 1984)),
                              GioiTinh.NU if nu else GioiTinh.NAM, dia_chi, _sdt(rnd),
                              f"ph{dem_ph[0]:03d}@mail.example.com" if rnd.random() < 0.4 else "",
                              quan_he, rnd.choice(NGHE))
            ht.phu_huynh[ma] = ph
            kq.append(ph)
        return kq

    def tao_hs(lop: LopHoc, khoi: int, dac_biet: bool = False) -> HocSinh:
        dem_hs[0] += 1
        ma = f"HS{dem_hs[0]:03d}"
        nu = rnd.random() < 0.5
        if dac_biet:
            ten, ns, gt, dc, sdt, mail, nu = ("Nguyễn Minh An", date(nam - 16, 3, 15), GioiTinh.NAM, "Hải Phòng",
                                              "0901112233", "an@mail.com", False)
        else:
            ten = _ten(rnd, nu)
            ns = _ngay_ngau_nhien(rnd, nam - 6 - khoi)
            gt, dc = (GioiTinh.NU if nu else GioiTinh.NAM), _dia_chi(rnd)
            sdt = _sdt(rnd) if rnd.random() < 0.6 else ""
            w = bo_dau(ten).lower().split()
            mail = f"{w[-1]}.{''.join(x[0] for x in w[:-1])}{dem_hs[0]:03d}@hs.truong.edu.vn" if rnd.random() < 0.7 else ""
        cccd = ("031" + "".join(str(rnd.randint(0, 9)) for _ in range(9))) if (khoi >= 11 and rnd.random() < 0.6) else ""
        hs = HocSinh(ma, ten, ns, gt, dc, sdt, mail, date(nam - (khoi - 10), 9, 5), TrangThaiHocSinh.DANG_HOC,
                     "Hải Phòng" if dac_biet else rnd.choice(NOI_SINH), "Kinh" if rnd.random() < 0.97 else "Tày", cccd)
        hs.ho_so.cap_nhat_ho_so(rnd.choice(SUC_KHOE), rnd.choice(THANH_TICH),
                                "Khiển trách do đi học muộn nhiều lần" if rnd.random() < 0.025 else "")
        ht.hoc_sinh[ma] = hs
        for ph in tao_phu_huynh(ten.split()[0], dc, dac_biet):
            hs.them_phu_huynh(ph)
        if lop is not None:
            lop.them_hoc_sinh(hs, bat_dau)
        _tai_khoan(ht, hs, ma.lower(), "hs123", VaiTro.HOC_SINH)
        if hs.phu_huynh:
            _tai_khoan(ht, hs.phu_huynh[0], hs.phu_huynh[0].ma.lower(), "ph123", VaiTro.PHU_HUYNH)
        nang_luc[ma] = min(9.6, max(3.5, rnd.gauss(6.9, 1.1)))
        return hs

    for lop in lops:
        for i in range(rnd.randint(33, 38)):
            tao_hs(lop, lop.khoi, dac_biet=(lop.ma_lop == "10A1" and i == 0))

    # vài học sinh chuyển lớp trong năm (để có lịch sử lớp)
    for hs in rnd.sample(lops[1].danh_sach_hoc_sinh(), 3):
        hs.chuyen_lop(lops[2], bat_dau + timedelta(days=30))

    # học sinh bảo lưu / chuyển trường / đã tốt nghiệp
    for kieu, so, den_ngay in ((TrangThaiHocSinh.BAO_LUU, 3, 25), (TrangThaiHocSinh.CHUYEN_TRUONG, 3, 45)):
        for _ in range(so):
            lop = rnd.choice(lops)
            hs = tao_hs(lop, lop.khoi)
            lop.xoa_hoc_sinh(hs, bat_dau + timedelta(days=den_ngay))
            hs.trang_thai = kieu
            nang_luc.pop(hs.ma, None)
            if hs.tai_khoan:
                hs.tai_khoan.hoat_dong = False
    for _ in range(4):
        hs = tao_hs(None, 12)
        hs.ngay_sinh = _ngay_ngau_nhien(rnd, nam - 19)
        hs.ngay_nhap_hoc = date(nam - 3, 9, 5)
        hs.trang_thai = TrangThaiHocSinh.DA_TOT_NGHIEP
        hs.ho_so.cap_nhat_ho_so(thanh_tich="Tốt nghiệp THPT năm " + str(nam))
        nang_luc.pop(hs.ma, None)

    # ---------------- điểm, hạnh kiểm ----------------
    for hk in nh.hoc_ky:
        if hk.ngay_bat_dau > hom_nay:
            continue
        troi_qua = (min(hom_nay, hk.ngay_ket_thuc) - hk.ngay_bat_dau).days
        so_tx = 0 if troi_qua < 14 else 1 if troi_qua < 28 else 2 if troi_qua < 42 else 3
        co_gk = troi_qua >= 45
        co_ck = hom_nay >= hk.ngay_ket_thuc - timedelta(days=14)
        for lop in lops:
            for hs in lop.danh_sach_hoc_sinh():
                nl = nang_luc[hs.ma]
                for mon in ht.mon_hoc.values():
                    cs = nl + rnd.gauss(0, 0.6)
                    for k in range(so_tx):
                        hs.diem.append(Diem(hs, mon, hk, LoaiDiem.THUONG_XUYEN, _buoc(cs + rnd.gauss(0, 0.8), 0.5),
                                            hk.ngay_bat_dau + timedelta(days=18 + 14 * k)))
                    if co_gk:
                        hs.diem.append(Diem(hs, mon, hk, LoaiDiem.GIUA_KY, _buoc(cs + rnd.gauss(0, 0.8), 0.25),
                                            hk.ngay_bat_dau + timedelta(days=46)))
                    if co_ck:
                        hs.diem.append(Diem(hs, mon, hk, LoaiDiem.CUOI_KY, _buoc(cs + rnd.gauss(0, 0.9), 0.25),
                                            min(hom_nay, hk.ngay_ket_thuc - timedelta(days=7))))
                if co_gk or co_ck:
                    r = rnd.random() + (nl - 6.9) * 0.08
                    xl = (XepLoaiHanhKiem.TOT if r > 0.4 else XepLoaiHanhKiem.KHA if r > 0.08
                          else XepLoaiHanhKiem.TRUNG_BINH if r > -0.1 else XepLoaiHanhKiem.YEU)
                    nx = {XepLoaiHanhKiem.TOT: "Ngoan, chăm chỉ, tích cực tham gia hoạt động lớp.",
                          XepLoaiHanhKiem.KHA: "Cần phát huy thêm tính tự giác.",
                          XepLoaiHanhKiem.TRUNG_BINH: "Cần chú ý nội quy, đi học đúng giờ.",
                          XepLoaiHanhKiem.YEU: "Cần phối hợp chặt chẽ với gia đình để cải thiện."}[xl]
                    hs.ket_qua_hanh_kiem.append(KetQuaHanhKiem(hs, hk, xl, nx))

    # ---------------- điểm danh ~ 30 ngày học gần nhất ----------------
    cuoi = min(hom_nay - timedelta(days=1), nh.ngay_ket_thuc)
    dau = max(bat_dau + timedelta(days=7), cuoi - timedelta(days=41))
    ngay_hoc, d = [], dau
    while d <= cuoi:
        if d.weekday() < 5:
            ngay_hoc.append(d)
        d += timedelta(days=1)
    ly_do = ["Ốm", "Việc gia đình", "Khám bệnh", "Đi viện", "Có đám hiếu"]
    for lop in lops:
        for hs in lop.danh_sach_hoc_sinh():
            p_vang = rnd.choice([0.01] * 7 + [0.04, 0.08])
            for ng in ngay_hoc:
                r = rnd.random()
                if r < p_vang * 0.6:
                    tt, gc = TrangThaiDiemDanh.VANG_CO_PHEP, rnd.choice(ly_do)
                elif r < p_vang:
                    tt, gc = TrangThaiDiemDanh.VANG_KHONG_PHEP, ""
                elif r < p_vang + 0.025:
                    tt, gc = TrangThaiDiemDanh.DI_MUON, "Đến sau tiết 1"
                else:
                    tt, gc = TrangThaiDiemDanh.CO_MAT, ""
                hs.diem_danh.append(DiemDanh(hs, lop, ng, tt, gc))
