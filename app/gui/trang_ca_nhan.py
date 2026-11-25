# -*- coding: utf-8 -*-
"""Các trang dành cho Học sinh / Phụ huynh (chỉ xem)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..enums import VaiTro
from .nen import MAU_NEN, MAU_PHU


class TrangCaNhan:
    def _chon_con(self, p, khi_doi):
        """Trả về hàm lay_hs(); phụ huynh nhiều con sẽ có ô chọn."""
        tk_ = self.ht.tai_khoan_hien_tai
        chu = tk_.chu_so_huu
        ds = [chu] if tk_.vai_tro is VaiTro.HOC_SINH else list(chu.hoc_sinh)
        if not ds:
            tk.Label(p, text="Tài khoản chưa liên kết với học sinh nào.", bg=MAU_NEN, fg=MAU_PHU).pack(pady=30)
            return None
        v = tk.StringVar(value=self.nhan_hs(ds[0]))
        if len(ds) > 1:
            hang = tk.Frame(p, bg=MAU_NEN)
            hang.pack(fill="x", pady=(0, 8))
            self.thanh_chon(hang, "Con:", v, [self.nhan_hs(h) for h in ds], 28, khi_doi)
        return lambda: self.hs_tu_nhan(v.get())

    def trang_thong_tin_ca_nhan(self, p) -> None:
        kv = self.the(p)
        holder = {}

        def ve():
            for w in kv.winfo_children():
                w.destroy()
            ngoai, trong = self.khung_cuon(kv)
            ngoai.pack(fill="both", expand=True)
            self.dung_the_thong_tin(trong, holder["lay"]())
        lay = self._chon_con(p, ve)
        if lay is None:
            kv.destroy()
            return
        holder["lay"] = lay
        kv.pack(fill="both", expand=True)
        ve()

    def trang_xem_diem(self, p) -> None:
        ds_nap = []
        lay = self._chon_con(p, lambda: [f() for f in ds_nap])
        if lay is None:
            return
        the = self.the(p)
        the.pack(fill="both", expand=True)
        ds_nap.append(self.dung_bang_diem(the, lay))

    def trang_xem_diem_danh(self, p) -> None:
        ds_nap = []
        lay = self._chon_con(p, lambda: [f() for f in ds_nap])
        if lay is None:
            return
        the = self.the(p)
        the.pack(fill="both", expand=True)
        ds_nap.append(self.dung_diem_danh_hs(the, lay))
