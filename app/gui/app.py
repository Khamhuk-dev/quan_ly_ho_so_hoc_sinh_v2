# -*- coding: utf-8 -*-
"""Cửa sổ chính: ghép các trang (mixin) lại với nhau."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from ..config import TEN_UNG_DUNG
from ..services import HeThong
from .nen import MAU_NEN, NenGUI
from .trang_ca_nhan import TrangCaNhan
from .trang_diem import TrangDiem
from .trang_diem_danh import TrangDiemDanh
from .trang_hoc_sinh import TrangHocSinh
from .trang_quan_tri import TrangQuanTri
from .trang_thong_ke import TrangThongKe
from .trang_tong_quan import TrangTongQuan


class UngDungGUI(NenGUI, TrangTongQuan, TrangHocSinh, TrangDiem, TrangDiemDanh, TrangThongKe, TrangQuanTri,
                 TrangCaNhan, tk.Tk):
    def __init__(self, ht: HeThong):
        tk.Tk.__init__(self)
        self.ht = ht
        self._lam_moi = None
        self._vung_cuon = []
        self.title(TEN_UNG_DUNG)
        self.geometry("1200x780")
        self.minsize(1060, 660)
        self.configure(bg=MAU_NEN)
        self.thiet_lap_kieu()
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_all(ev, self._cuon_chuot)
        self.protocol("WM_DELETE_WINDOW", self.thoat)
        self.hien_dang_nhap()
        if ht.thong_bao_khoi_dong:
            self.after(400, lambda: messagebox.showwarning("Thông báo khởi động", "\n\n".join(ht.thong_bao_khoi_dong),
                                                           parent=self))
