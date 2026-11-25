# -*- coding: utf-8 -*-
"""«service» DichVuBaoCao: chỉ *sử dụng* HocSinh, LopHoc, HocKy - không lưu dữ liệu."""
from __future__ import annotations

from typing import Dict, List, Optional

from .enums import GioiTinh, TrangThaiDiemDanh, TrangThaiHocSinh
from .models import HocKy, HocSinh, LopHoc, MonHoc
from .utils import bo_dau, xep_loai_hoc_luc

HOC_LUC = ("Giỏi", "Khá", "Trung bình", "Yếu")


def ten_cuoi(ho_ten: str) -> str:
    return bo_dau(ho_ten.split()[-1]).lower() if ho_ten.split() else ""


class DichVuBaoCao:
    @staticmethod
    def phan_bo_hoc_luc(ds_hs: List[HocSinh], hoc_ky: Optional[HocKy]) -> Dict[str, int]:
        dem = {k: 0 for k in HOC_LUC}
        if hoc_ky is None:
            return dem
        for h in ds_hs:
            dtb = h.tinh_diem_trung_binh(hoc_ky)
            if dtb:
                dem[xep_loai_hoc_luc(dtb)] += 1
        return dem

    @staticmethod
    def ty_le_chuyen_can(ds_hs: List[HocSinh], tu=None, den=None) -> Optional[float]:
        co, tong = 0, 0
        for h in ds_hs:
            t = h.thong_ke_diem_danh(tu, den)
            co += t[TrangThaiDiemDanh.CO_MAT] + t[TrangThaiDiemDanh.DI_MUON]
            tong += sum(t.values())
        return 100.0 * co / tong if tong else None

    @staticmethod
    def xep_hang_lop(lop: LopHoc, hoc_ky: HocKy) -> List[tuple]:
        """[(hạng, học sinh, ĐTB)] sắp theo ĐTB giảm dần; đồng điểm cùng hạng."""
        ds = sorted(((h, h.tinh_diem_trung_binh(hoc_ky)) for h in lop.danh_sach_hoc_sinh()),
                    key=lambda x: (-x[1], ten_cuoi(x[0].ho_ten)))
        kq, hang, truoc = [], 0, None
        for i, (h, d) in enumerate(ds, 1):
            if d != truoc:
                hang, truoc = i, d
            kq.append((hang if d else "-", h, d))
        return kq

    @staticmethod
    def bao_cao_hoc_sinh(hs: HocSinh, hoc_ky: HocKy) -> str:
        lop = hs.lop_hien_tai
        dong = [f"BÁO CÁO HỌC SINH: {hs.ho_ten} ({hs.ma_hoc_sinh}) - {hoc_ky}",
                f"Lớp: {lop.ten_lop if lop else '(chưa xếp lớp)'}   Trạng thái: {hs.trang_thai.value}", "-" * 70]
        mons = sorted({d.mon_hoc for d in hs.diem if d.hoc_ky is hoc_ky}, key=lambda m: m.ma_mon)
        for m in mons:
            chi_tiet = ", ".join(f"{d.loai_diem.value}: {d.gia_tri:g}"
                                 for d in hs.diem if d.mon_hoc is m and d.hoc_ky is hoc_ky)
            dong.append(f"{m.ten_mon:<14} TB môn: {hs.diem_mon(m, hoc_ky):>5.2f}   [{chi_tiet}]")
        if not mons:
            dong.append("(Chưa có điểm)")
        else:
            dtb = hs.tinh_diem_trung_binh(hoc_ky)
            dong.append(f"Điểm trung bình: {dtb:.2f} - Học lực: {xep_loai_hoc_luc(dtb)}")
            if lop:
                hang = next((x[0] for x in DichVuBaoCao.xep_hang_lop(lop, hoc_ky) if x[1] is hs), "-")
                dong.append(f"Xếp hạng trong lớp: {hang}/{lop.dem_si_so()}")
        hk = hs.hanh_kiem_hoc_ky(hoc_ky)
        dong.append("Hạnh kiểm: " + (f"{hk.xep_loai.value} - {hk.nhan_xet}" if hk else "(chưa xếp loại)"))
        tk = hs.thong_ke_diem_danh(hoc_ky.ngay_bat_dau, hoc_ky.ngay_ket_thuc)
        dong.append("Điểm danh: " + ", ".join(f"{t.value} {n}" for t, n in tk.items()))
        return "\n".join(dong)

    @staticmethod
    def bao_cao_lop(lop: LopHoc, hoc_ky: HocKy) -> str:
        dong = [f"BÁO CÁO LỚP {lop.ten_lop} - {hoc_ky} - Sĩ số {lop.dem_si_so()}/{lop.si_so_toi_da}",
                f"GVCN: {lop.giao_vien_chu_nhiem.ho_ten if lop.giao_vien_chu_nhiem else '-'}",
                f"{'Hạng':<6}{'Mã HS':<9}{'Họ tên':<28}{'ĐTB':>6}  {'Học lực':<11}Hạnh kiểm", "-" * 74]
        dem = {k: 0 for k in HOC_LUC}
        for hang, hs, dtb in DichVuBaoCao.xep_hang_lop(lop, hoc_ky):
            hk = hs.hanh_kiem_hoc_ky(hoc_ky)
            hl = xep_loai_hoc_luc(dtb) if dtb else "-"
            if dtb:
                dem[hl] += 1
            dong.append(f"{hang!s:<6}{hs.ma_hoc_sinh:<9}{hs.ho_ten:<28}{dtb:>6.2f}  {hl:<11}"
                        f"{hk.xep_loai.value if hk else '-'}")
        dong += ["-" * 74, "Tổng kết học lực: " + ", ".join(f"{k} {v}" for k, v in dem.items())]
        return "\n".join(dong)

    @staticmethod
    def bao_cao_mon(lop: LopHoc, mon: MonHoc, hoc_ky: HocKy) -> str:
        gv = lop.giao_vien_day(mon)
        dong = [f"BẢNG ĐIỂM MÔN {mon.ten_mon.upper()} - LỚP {lop.ten_lop} - {hoc_ky}",
                f"Giáo viên: {gv.ho_ten if gv else '-'}",
                f"{'Mã HS':<9}{'Họ tên':<28}{'TX':<24}{'GK':>5}{'CK':>5}{'TB':>7}", "-" * 78]
        tong, so = 0.0, 0
        for hs in sorted(lop.danh_sach_hoc_sinh(), key=lambda h: (ten_cuoi(h.ho_ten), h.ma)):
            ds = [d for d in hs.diem if d.mon_hoc is mon and d.hoc_ky is hoc_ky]
            tx = ", ".join(f"{d.gia_tri:g}" for d in ds if d.loai_diem.name == "THUONG_XUYEN")
            gk = next((f"{d.gia_tri:g}" for d in ds if d.loai_diem.name == "GIUA_KY"), "-")
            ck = next((f"{d.gia_tri:g}" for d in ds if d.loai_diem.name == "CUOI_KY"), "-")
            tb = hs.diem_mon(mon, hoc_ky)
            if tb is not None:
                tong, so = tong + tb, so + 1
            dong.append(f"{hs.ma_hoc_sinh:<9}{hs.ho_ten:<28}{tx or '-':<24}{gk:>5}{ck:>5}"
                        f"{(f'{tb:.2f}' if tb is not None else '-'):>7}")
        dong += ["-" * 78, f"Điểm trung bình môn của lớp: {tong / so:.2f}" if so else "(Chưa có điểm)"]
        return "\n".join(dong)

    @staticmethod
    def bao_cao_diem_danh(lop: LopHoc, hoc_ky: HocKy) -> str:
        dong = [f"BÁO CÁO ĐIỂM DANH LỚP {lop.ten_lop} - {hoc_ky}",
                f"{'Mã HS':<9}{'Họ tên':<28}{'Có mặt':>7}{'V.phép':>8}{'V.KP':>6}{'Muộn':>6}{'Chuyên cần':>12}", "-" * 76]
        for hs in sorted(lop.danh_sach_hoc_sinh(), key=lambda h: h.ma):
            t = hs.thong_ke_diem_danh(hoc_ky.ngay_bat_dau, hoc_ky.ngay_ket_thuc, lop)
            tong = sum(t.values())
            cc = f"{100 * (t[TrangThaiDiemDanh.CO_MAT] + t[TrangThaiDiemDanh.DI_MUON]) / tong:.0f}%" if tong else "-"
            dong.append(f"{hs.ma_hoc_sinh:<9}{hs.ho_ten:<28}{t[TrangThaiDiemDanh.CO_MAT]:>7}"
                        f"{t[TrangThaiDiemDanh.VANG_CO_PHEP]:>8}{t[TrangThaiDiemDanh.VANG_KHONG_PHEP]:>6}"
                        f"{t[TrangThaiDiemDanh.DI_MUON]:>6}{cc:>12}")
        return "\n".join(dong)

    @staticmethod
    def thong_ke(ds_hs: List[HocSinh], ds_lop: List[LopHoc], hoc_ky: Optional[HocKy]) -> str:
        dong = [f"THỐNG KÊ TỔNG QUÁT - Tổng số học sinh: {len(ds_hs)}", "", "Theo lớp:"]
        for l in sorted(ds_lop, key=lambda x: x.ma_lop):
            dong.append(f"  {l.ten_lop:<10}: {l.dem_si_so()}/{l.si_so_toi_da}")
        dong.append("Theo giới tính:")
        for g in GioiTinh:
            dong.append(f"  {g.value:<10}: {sum(1 for h in ds_hs if h.gioi_tinh is g)}")
        dong.append("Theo trạng thái:")
        for t in TrangThaiHocSinh:
            dong.append(f"  {t.value:<14}: {sum(1 for h in ds_hs if h.trang_thai is t)}")
        if hoc_ky:
            dong.append(f"Học lực {hoc_ky}:")
            dong += [f"  {k:<10}: {v}" for k, v in DichVuBaoCao.phan_bo_hoc_luc(ds_hs, hoc_ky).items()]
            dong.append(f"Điểm TB theo khối ({hoc_ky.ten_hoc_ky}):")
            for khoi in sorted({l.khoi for l in ds_lop}):
                hs_khoi = [h for l in ds_lop if l.khoi == khoi for h in l.danh_sach_hoc_sinh()]
                v = [d for d in (h.tinh_diem_trung_binh(hoc_ky) for h in hs_khoi) if d]
                dong.append(f"  Khối {khoi:<4}: {sum(v) / len(v):.2f}" if v else f"  Khối {khoi:<4}: -")
        cc = DichVuBaoCao.ty_le_chuyen_can(ds_hs)
        if cc is not None:
            dong.append(f"Tỷ lệ chuyên cần toàn trường: {cc:.1f}%")
        return "\n".join(dong)
