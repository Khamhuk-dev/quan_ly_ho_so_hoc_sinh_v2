# -*- coding: utf-8 -*-
"""Trang Thống kê, báo cáo."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..enums import TrangThaiHocSinh
from ..reports import DichVuBaoCao, ten_cuoi
from ..utils import LoiNghiepVu
from .nen import FONT, MAU_NEN

LOAI = ["Thống kê tổng quát", "Báo cáo lớp (xếp hạng)", "Bảng điểm theo môn", "Điểm danh theo lớp", "Báo cáo học sinh"]


class TrangThongKe:
    def trang_thong_ke(self, p) -> None:
        ht = self.ht
        self.v_bc, self.v_bc_lop = tk.StringVar(value=LOAI[0]), tk.StringVar()
        self.v_bc_hk, self.v_bc_mon, self.v_bc_hs = tk.StringVar(), tk.StringVar(), tk.StringVar()
        hk0 = ht.hoc_ky_hien_tai()
        self.v_bc_hk.set(str(hk0) if hk0 else "")
        lops = [self.nhan_lop(l) for l in sorted(ht.lop_hoc.values(), key=lambda x: x.ma_lop)]
        self.v_bc_lop.set(lops[0] if lops else "")
        h1 = tk.Frame(p, bg=MAU_NEN)
        h1.pack(fill="x", pady=(0, 6))
        self.thanh_chon(h1, "Loại báo cáo:", self.v_bc, LOAI, 24)
        self.thanh_chon(h1, "Học kỳ:", self.v_bc_hk, [str(h) for h in ht.hoc_ky_tat_ca()], 22)
        h2 = tk.Frame(p, bg=MAU_NEN)
        h2.pack(fill="x", pady=(0, 8))
        self.thanh_chon(h2, "Lớp:", self.v_bc_lop, lops, 14, self.doi_lop_bc)
        self.cb_bc_mon = self.thanh_chon(h2, "Môn:", self.v_bc_mon, [f"{m.ma_mon} - {m.ten_mon}" for m in ht.mon_hoc.values()], 14)
        self.cb_bc_hs = self.thanh_chon(h2, "Học sinh:", self.v_bc_hs, [], 26)
        self.nut(h2, "Xem báo cáo", self.xem_bao_cao, "Primary").pack(side="left", padx=(0, 8))
        self.nut(h2, "Lưu ra tệp .txt", self.luu_bao_cao).pack(side="left")
        the = self.the(p, padding=8)
        the.pack(fill="both", expand=True)
        self.txt = tk.Text(the, wrap="none", font=("Consolas", 10), relief="flat", bd=0)
        sy = ttk.Scrollbar(the, orient="vertical", command=self.txt.yview)
        sx = ttk.Scrollbar(the, orient="horizontal", command=self.txt.xview)
        self.txt.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.txt.pack(fill="both", expand=True)
        self.doi_lop_bc()
        self.xem_bao_cao()

    def doi_lop_bc(self) -> None:
        lop = self.lop_tu_nhan(self.v_bc_lop.get())
        ds = [self.nhan_hs(h) for h in sorted(lop.danh_sach_hoc_sinh(), key=lambda h: (ten_cuoi(h.ho_ten), h.ma))] if lop else []
        self.cb_bc_hs["values"] = ds
        self.v_bc_hs.set(ds[0] if ds else "")

    def tao_bao_cao(self) -> str:
        ht, loai = self.ht, self.v_bc.get()
        hk, lop = self.hk_tu_nhan(self.v_bc_hk.get()), self.lop_tu_nhan(self.v_bc_lop.get())
        if loai == LOAI[0]:
            return DichVuBaoCao.thong_ke([h for l in ht.lop_hoc.values() for h in l.danh_sach_hoc_sinh()] or [],
                                         list(ht.lop_hoc.values()), hk) + "\n" + "\n".join(
                f"Tổng hồ sơ {t.value}: {n}" for t, n in
                ((t, sum(1 for h in ht.hoc_sinh.values() if h.trang_thai is t)) for t in TrangThaiHocSinh))
        if lop is None or hk is None:
            raise LoiNghiepVu("Hãy chọn lớp và học kỳ.")
        if loai == LOAI[1]:
            return DichVuBaoCao.bao_cao_lop(lop, hk)
        if loai == LOAI[2]:
            mon = ht.mon_hoc.get(self.v_bc_mon.get().split(" - ")[0])
            if mon is None:
                raise LoiNghiepVu("Hãy chọn môn học.")
            return DichVuBaoCao.bao_cao_mon(lop, mon, hk)
        if loai == LOAI[3]:
            return DichVuBaoCao.bao_cao_diem_danh(lop, hk)
        hs = self.hs_tu_nhan(self.v_bc_hs.get())
        if hs is None:
            raise LoiNghiepVu("Hãy chọn học sinh.")
        return DichVuBaoCao.bao_cao_hoc_sinh(hs, hk)

    def xem_bao_cao(self) -> None:
        try:
            nd = self.tao_bao_cao()
        except LoiNghiepVu as e:
            self.loi(e)
            return
        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", nd)

    def luu_bao_cao(self) -> None:
        d = self.chon_noi_luu("bao_cao.txt", ".txt", "Văn bản")
        if d:
            with open(d, "w", encoding="utf-8-sig") as f:
                f.write(self.txt.get("1.0", "end"))
            self.thanh_cong("Đã lưu: " + d)
