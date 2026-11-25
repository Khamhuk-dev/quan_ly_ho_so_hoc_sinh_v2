# -*- coding: utf-8 -*-
"""Trang Tổng quan (dashboard)."""
from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import ttk

from ..utils import chuoi_ngay
from .nen import FONT, MAU_BIEU_DO, MAU_CHINH, MAU_CHU, MAU_NEN, MAU_NGUY_HIEM, MAU_PHU


class TrangTongQuan:
    def the_so(self, cha, tieu_de: str, gia_tri: str, phu: str = "", mau: str = MAU_CHINH) -> tk.Frame:
        f = tk.Frame(cha, bg="white", padx=16, pady=10, highlightbackground="#e2e8f0", highlightthickness=1)
        tk.Label(f, text=tieu_de, bg="white", fg=MAU_PHU, font=(FONT, 9)).pack(anchor="w")
        tk.Label(f, text=gia_tri, bg="white", fg=mau, font=(FONT, 22, "bold")).pack(anchor="w")
        tk.Label(f, text=phu, bg="white", fg=MAU_PHU, font=(FONT, 9)).pack(anchor="w")
        return f

    def trang_tong_quan(self, p) -> None:
        ht = self.ht
        lops = self.ds_lop_duoc_quan_ly()
        tq = ht.tong_quan(lops)
        hk = tq["hoc_ky"]
        tk.Label(p, bg=MAU_NEN, fg=MAU_PHU, anchor="w", font=(FONT, 10),
                 text=f"Xin chào, {ht.tai_khoan_hien_tai.chu_so_huu.ho_ten}.  Hôm nay {chuoi_ngay(date.today())}"
                      + (f"  ·  {hk}" if hk else "")).pack(fill="x", pady=(0, 8))

        hang = tk.Frame(p, bg=MAU_NEN)
        hang.pack(fill="x")
        dtb = tq["dtb_truong"]
        cc = tq["chuyen_can"]
        cards = [
            ("Học sinh đang học", str(tq["so_hs_dang_hoc"]), f"Tổng hồ sơ: {tq['so_hs_tong']}", MAU_CHINH),
            ("Lớp học / Giáo viên", f"{tq['so_lop']} / {tq['so_gv'] - (1 if 'GV00' in ht.giao_vien else 0)}",
             "lớp phụ trách / giáo viên", "#7c3aed"),
            ("Điểm TB học kỳ", f"{dtb:.2f}" if dtb else "-", hk.ten_hoc_ky if hk else "", "#16a34a"),
            ("Chuyên cần (30 ngày)", f"{cc:.1f}%" if cc is not None else "-", "có mặt + đi muộn", "#0891b2"),
            ("Cần quan tâm", str(len(tq["can_chu_y"])), "ĐTB < 5 hoặc vắng KP", MAU_NGUY_HIEM),
        ]
        for i, (a, b, c, m) in enumerate(cards):
            self.the_so(hang, a, b, c, m).grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            hang.columnconfigure(i, weight=1, uniform="the")

        bd = tk.Frame(p, bg=MAU_NEN)
        bd.pack(fill="x", pady=10)
        bd.columnconfigure(0, weight=3, uniform="bd")
        bd.columnconfigure(1, weight=2, uniform="bd")
        c1 = tk.Canvas(bd, height=190, bg="white", highlightthickness=0)
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        c2 = tk.Canvas(bd, height=190, bg="white", highlightthickness=0)
        c2.grid(row=0, column=1, sticky="nsew")
        self.ve_cot(c1, "Sĩ số theo lớp", [x[0] for x in tq["si_so"]], [x[1] for x in tq["si_so"]],
                    toi_da=max([x[2] for x in tq["si_so"]] or [1]))
        self.ve_banh(c2, f"Phân bố học lực{' - ' + hk.ten_hoc_ky if hk else ''}", tq["phan_bo_hoc_luc"])

        duoi = tk.Frame(p, bg=MAU_NEN)
        duoi.pack(fill="both", expand=True)
        duoi.columnconfigure(0, weight=3, uniform="d")
        duoi.columnconfigure(1, weight=2, uniform="d")
        duoi.rowconfigure(0, weight=1)
        trai = self.the(duoi, padding=10)
        trai.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(trai, text="Học sinh cần quan tâm", style="Card.TLabel", font=(FONT, 11, "bold")).pack(anchor="w", pady=(0, 6))
        b1 = self.tao_bang(trai, [("ma", "Mã", 70), ("ten", "Họ tên", 170), ("lop", "Lớp", 60), ("ly", "Lý do", 240)], cao=5)
        self.do_bang(b1, [(h.ma, (h.ma, h.ho_ten, h.lop_hien_tai.ten_lop if h.lop_hien_tai else "-", ly))
                          for h, ly in tq["can_chu_y"]])
        phai = self.the(duoi, padding=10)
        phai.grid(row=0, column=1, sticky="nsew")
        if ht.la_quan_tri():
            ttk.Label(phai, text="Hoạt động gần đây", style="Card.TLabel", font=(FONT, 11, "bold")).pack(anchor="w", pady=(0, 6))
            b2 = self.tao_bang(phai, [("tg", "Thời gian", 120), ("nguoi", "Người dùng", 70), ("hd", "Hành động", 140)], cao=5)
            self.do_bang(b2, [(str(i), (r[0][5:16].replace("-", "/"), r[1], r[2]))
                              for i, r in enumerate(ht.kho.doc_nhat_ky(12))])
        else:
            ttk.Label(phai, text="Lớp tôi phụ trách", style="Card.TLabel", font=(FONT, 11, "bold")).pack(anchor="w", pady=(0, 6))
            gv = ht.tai_khoan_hien_tai.chu_so_huu
            b2 = self.tao_bang(phai, [("lop", "Lớp", 60), ("ss", "Sĩ số", 60), ("vt", "Vai trò", 140)], cao=5)
            self.do_bang(b2, [(l.ma_lop, (l.ten_lop, f"{l.dem_si_so()}/{l.si_so_toi_da}",
                                          "Chủ nhiệm" if l.giao_vien_chu_nhiem is gv else "Bộ môn: " + ", ".join(
                                              x.mon_hoc.ten_mon for x in gv.phan_cong
                                              if x.lop_hoc is l and x.ngay_ket_thuc is None)))
                              for l in lops])
