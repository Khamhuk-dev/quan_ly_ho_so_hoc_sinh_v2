# -*- coding: utf-8 -*-
"""Trang Điểm danh."""
from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk

from ..enums import TrangThaiDiemDanh
from ..reports import ten_cuoi
from ..utils import LoiNghiepVu, chuoi_ngay, ngay_hop_le
from .nen import FONT, MAU_CHINH, MAU_NEN, MAU_PHU, enum_tu_nhan, nhan_enum
from .trang_hoc_sinh import THU


class TrangDiemDanh:
    def trang_diem_danh(self, p) -> None:
        lops = self.ds_lop_duoc_quan_ly()
        if not lops:
            tk.Label(p, text="Bạn chưa được phân công lớp nào.", bg=MAU_NEN, fg=MAU_PHU).pack(pady=30)
            return
        self.v_dd_lop = tk.StringVar(value=self.nhan_lop(lops[0]))
        self.v_dd_ngay = tk.StringVar(value=chuoi_ngay(date.today()))
        top = tk.Frame(p, bg=MAU_NEN)
        top.pack(fill="x", pady=(0, 8))
        self.thanh_chon(top, "Lớp:", self.v_dd_lop, [self.nhan_lop(l) for l in lops], 14, self.nap_diem_danh)
        ttk.Label(top, text="Ngày:").pack(side="left")
        self.nut(top, "◀", lambda: self.doi_ngay_dd(-1)).pack(side="left", padx=(6, 2))
        e = ttk.Entry(top, textvariable=self.v_dd_ngay, width=12, justify="center")
        e.pack(side="left")
        e.bind("<Return>", lambda _e: self.nap_diem_danh())
        self.nut(top, "▶", lambda: self.doi_ngay_dd(1)).pack(side="left", padx=(2, 6))
        self.nut(top, "Hôm nay", lambda: (self.v_dd_ngay.set(chuoi_ngay(date.today())), self.nap_diem_danh())).pack(side="left")
        hang = tk.Frame(p, bg=MAU_NEN)
        hang.pack(fill="x", pady=(0, 8))
        self.nut(hang, "💾 Lưu điểm danh", self.luu_diem_danh_gui, "Primary").pack(side="left", padx=(0, 8))
        self.nut(hang, "Tất cả có mặt", self.tat_ca_co_mat).pack(side="left", padx=(0, 12))
        self.lb_dd = tk.Label(hang, bg=MAU_NEN, fg=MAU_PHU, font=(FONT, 10))
        self.lb_dd.pack(side="left")
        self.kv_dd = ttk.Frame(p, style="Card.TFrame")
        self.kv_dd.pack(fill="both", expand=True)
        self._lam_moi = self.nap_diem_danh
        self.nap_diem_danh()

    def doi_ngay_dd(self, so: int) -> None:
        try:
            d = ngay_hop_le(self.v_dd_ngay.get(), "Ngày") + timedelta(days=so)
        except LoiNghiepVu:
            d = date.today()
        self.v_dd_ngay.set(chuoi_ngay(d))
        self.nap_diem_danh()

    def nap_diem_danh(self) -> None:
        for w in self.kv_dd.winfo_children():
            w.destroy()
        self.o_dd = {}
        lop = self.lop_tu_nhan(self.v_dd_lop.get())
        try:
            ngay = ngay_hop_le(self.v_dd_ngay.get(), "Ngày")
        except LoiNghiepVu as e:
            self.lb_dd.config(text=str(e))
            return
        ngoai, trong = self.khung_cuon(self.kv_dd)
        ngoai.pack(fill="both", expand=True)
        for c, t in enumerate(["Mã", "Họ tên", "Trạng thái", "Ghi chú"]):
            ttk.Label(trong, text=t, style="Card.TLabel", font=(FONT, 10, "bold")).grid(row=0, column=c, padx=6, pady=4, sticky="w")
        da_co = False
        for r, h in enumerate(sorted(lop.danh_sach_hoc_sinh(), key=lambda x: (ten_cuoi(x.ho_ten), x.ma)), 1):
            cu = next((d for d in h.diem_danh if d.lop_hoc is lop and d.ngay == ngay), None)
            da_co = da_co or cu is not None
            vt = tk.StringVar(value=(cu.trang_thai if cu else TrangThaiDiemDanh.CO_MAT).value)
            vg = tk.StringVar(value=cu.ghi_chu if cu else "")
            ttk.Label(trong, text=h.ma, style="Card.TLabel").grid(row=r, column=0, padx=6, sticky="w")
            ttk.Label(trong, text=h.ho_ten, style="Card.TLabel").grid(row=r, column=1, padx=6, sticky="w")
            cb = ttk.Combobox(trong, textvariable=vt, values=nhan_enum(TrangThaiDiemDanh), state="readonly", width=16)
            cb.grid(row=r, column=2, padx=6, pady=2)
            cb.bind("<<ComboboxSelected>>", lambda _e: self.dem_dd())
            ttk.Entry(trong, textvariable=vg, width=36).grid(row=r, column=3, padx=6, pady=2)
            self.o_dd[h.ma] = (vt, vg)
        self._da_diem_danh = da_co
        self.dem_dd()

    def dem_dd(self) -> None:
        dem = {t: 0 for t in TrangThaiDiemDanh}
        for vt, _ in self.o_dd.values():
            dem[enum_tu_nhan(TrangThaiDiemDanh, vt.get())] += 1
        try:
            ngay = ngay_hop_le(self.v_dd_ngay.get(), "Ngày")
            ds = f"{THU[ngay.weekday()]}  ·  " + ("đã điểm danh" if self._da_diem_danh else "chưa điểm danh")
        except LoiNghiepVu:
            ds = ""
        self.lb_dd.config(text=ds + "   |   " + "  ".join(f"{t.value}: {n}" for t, n in dem.items()))

    def tat_ca_co_mat(self) -> None:
        for vt, _ in self.o_dd.values():
            vt.set(TrangThaiDiemDanh.CO_MAT.value)
        self.dem_dd()

    def luu_diem_danh_gui(self) -> None:
        lop = self.lop_tu_nhan(self.v_dd_lop.get())
        try:
            ngay = ngay_hop_le(self.v_dd_ngay.get(), "Ngày")
            if ngay.weekday() >= 5 and not messagebox.askyesno("Cuối tuần", f"{chuoi_ngay(ngay)} là {THU[ngay.weekday()]}. Vẫn lưu?", parent=self):
                return
            tt = {ma: enum_tu_nhan(TrangThaiDiemDanh, vt.get()) for ma, (vt, _) in self.o_dd.items()}
            gc = {ma: vg.get().strip() for ma, (_, vg) in self.o_dd.items()}
            self.ht.luu_diem_danh(lop, ngay, tt, gc)
        except LoiNghiepVu as e:
            self.loi(e)
            return
        self.thanh_cong(f"Đã lưu điểm danh lớp {lop.ten_lop} ngày {chuoi_ngay(ngay)}.")
        self.nap_diem_danh()
