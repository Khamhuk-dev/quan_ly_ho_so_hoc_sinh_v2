# -*- coding: utf-8 -*-
"""Trang Nhập điểm (bảng điểm cả lớp) và Hạnh kiểm."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Optional

from ..enums import XepLoaiHanhKiem
from ..exporters import ghi_csv
from ..models import TRONG_SO_LOAI_DIEM
from ..enums import LoaiDiem
from ..reports import DichVuBaoCao, ten_cuoi
from ..utils import LoiNghiepVu, so_thuc_diem, xep_loai_hoc_luc
from .nen import FONT, MAU_CHINH, MAU_NEN, MAU_PHU, nhan_enum


class TrangDiem:
    def trang_diem(self, p) -> None:
        ht = self.ht
        lops = self.ds_lop_duoc_quan_ly()
        if not lops:
            tk.Label(p, text="Bạn chưa được phân công lớp nào.", bg=MAU_NEN, fg=MAU_PHU).pack(pady=30)
            return
        hks = [str(h) for h in ht.hoc_ky_tat_ca()]
        hk0 = ht.hoc_ky_hien_tai()
        self.v_d_lop = tk.StringVar(value=self.nhan_lop(lops[0]))
        self.v_d_hk = tk.StringVar(value=str(hk0) if hk0 else "")
        self.v_d_mon = tk.StringVar()
        top = tk.Frame(p, bg=MAU_NEN)
        top.pack(fill="x", pady=(0, 8))
        self.thanh_chon(top, "Lớp:", self.v_d_lop, [self.nhan_lop(l) for l in lops], 14, self.doi_lop_diem)
        self.thanh_chon(top, "Học kỳ:", self.v_d_hk, hks, 22, self.nap_tat_ca_diem)
        self.cb_d_mon = self.thanh_chon(top, "Môn:", self.v_d_mon, [], 14, self.nap_bang_diem)
        nb = ttk.Notebook(p)
        nb.pack(fill="both", expand=True)
        t1 = ttk.Frame(nb, style="Card.TFrame", padding=10)
        t2 = ttk.Frame(nb, style="Card.TFrame", padding=10)
        nb.add(t1, text="Nhập điểm theo môn")
        nb.add(t2, text="Hạnh kiểm")
        bar = ttk.Frame(t1, style="Card.TFrame")
        bar.pack(fill="x", pady=(0, 8))
        self.nut(bar, "💾 Lưu bảng điểm", self.luu_bang_diem, "Primary").pack(side="left", padx=(0, 8))
        self.nut(bar, "Tải lại", self.nap_bang_diem).pack(side="left", padx=(0, 8))
        self.nut(bar, "Xuất CSV", self.xuat_bang_diem_csv).pack(side="left")
        ttk.Label(bar, text="  Hệ số: thường xuyên ×1, giữa kỳ ×2, cuối kỳ ×3 · để trống nếu chưa có điểm",
                  style="Muted.TLabel").pack(side="left")
        self.kv_diem = ttk.Frame(t1, style="Card.TFrame")
        self.kv_diem.pack(fill="both", expand=True)
        bar2 = ttk.Frame(t2, style="Card.TFrame")
        bar2.pack(fill="x", pady=(0, 8))
        self.nut(bar2, "💾 Lưu hạnh kiểm", self.luu_hanh_kiem, "Primary").pack(side="left", padx=(0, 8))
        self.nut(bar2, "Tải lại", self.nap_hanh_kiem).pack(side="left")
        self.lb_hk_quyen = ttk.Label(bar2, text="", style="Muted.TLabel")
        self.lb_hk_quyen.pack(side="left", padx=10)
        self.kv_hk = ttk.Frame(t2, style="Card.TFrame")
        self.kv_hk.pack(fill="both", expand=True)
        self._lam_moi = self.nap_tat_ca_diem
        self.doi_lop_diem()

    # ---------------------------------------------------------------- chung
    def _chon_diem(self):
        return (self.lop_tu_nhan(self.v_d_lop.get()), self.ht.mon_hoc.get(self.v_d_mon.get().split(" - ")[0]),
                self.hk_tu_nhan(self.v_d_hk.get()))

    def doi_lop_diem(self) -> None:
        lop = self.lop_tu_nhan(self.v_d_lop.get())
        mons = [f"{m.ma_mon} - {m.ten_mon}" for m in self.ht.mon_duoc_nhap_diem(lop)]
        self.cb_d_mon["values"] = mons
        if self.v_d_mon.get() not in mons:
            self.v_d_mon.set(mons[0] if mons else "")
        self.nap_tat_ca_diem()

    def nap_tat_ca_diem(self) -> None:
        self.nap_bang_diem()
        self.nap_hanh_kiem()

    @staticmethod
    def _xoa_con(kv) -> None:
        for w in kv.winfo_children():
            w.destroy()

    # ---------------------------------------------------------------- bảng điểm
    def nap_bang_diem(self) -> None:
        self._xoa_con(self.kv_diem)
        lop, mon, hk = self._chon_diem()
        self.o_diem = {}
        if not (lop and mon and hk):
            ttk.Label(self.kv_diem, text="Chưa có môn nào để nhập điểm ở lớp này.", style="Muted.TLabel").pack(pady=20)
            return
        ds = sorted(lop.danh_sach_hoc_sinh(), key=lambda h: (ten_cuoi(h.ho_ten), h.ma))

        def tx_cua(h):
            return [d.gia_tri for d in h.diem if d.mon_hoc is mon and d.hoc_ky is hk and d.loai_diem is LoaiDiem.THUONG_XUYEN]
        n_tx = max([4] + [len(tx_cua(h)) for h in ds])
        ngoai, trong = self.khung_cuon(self.kv_diem)
        ngoai.pack(fill="both", expand=True)
        tieu = ["Mã", "Họ tên"] + [f"TX{i + 1}" for i in range(n_tx)] + ["GK", "CK", "TB môn"]
        for c, t in enumerate(tieu):
            ttk.Label(trong, text=t, style="Card.TLabel", font=(FONT, 10, "bold")).grid(row=0, column=c, padx=4, pady=4,
                                                                                         sticky="w" if c < 2 else "")
        fmt = lambda v: f"{v:g}"
        for r, h in enumerate(ds, 1):
            ttk.Label(trong, text=h.ma, style="Card.TLabel").grid(row=r, column=0, sticky="w", padx=4)
            ttk.Label(trong, text=h.ho_ten, style="Card.TLabel").grid(row=r, column=1, sticky="w", padx=4)
            tx = tx_cua(h)
            gk = next((d.gia_tri for d in h.diem if d.mon_hoc is mon and d.hoc_ky is hk and d.loai_diem is LoaiDiem.GIUA_KY), None)
            ck = next((d.gia_tri for d in h.diem if d.mon_hoc is mon and d.hoc_ky is hk and d.loai_diem is LoaiDiem.CUOI_KY), None)
            vtx = [tk.StringVar(value=fmt(tx[i]) if i < len(tx) else "") for i in range(n_tx)]
            vgk, vck = tk.StringVar(value=fmt(gk) if gk is not None else ""), tk.StringVar(value=fmt(ck) if ck is not None else "")
            lb = ttk.Label(trong, text="-", style="Card.TLabel", font=(FONT, 10, "bold"), foreground=MAU_CHINH)
            lb.grid(row=r, column=len(tieu) - 1, padx=8)
            for c, v in enumerate(vtx + [vgk, vck], 2):
                ttk.Entry(trong, textvariable=v, width=6, justify="center").grid(row=r, column=c, padx=3, pady=2)
                v.trace_add("write", lambda *_a, ex=(vtx, vgk, vck, lb): self._tinh_tb(*ex))
            self.o_diem[h.ma] = {"tx": vtx, "gk": vgk, "ck": vck}
            self._tinh_tb(vtx, vgk, vck, lb)

    @staticmethod
    def _tinh_tb(vtx, vgk, vck, lb) -> None:
        tong = tr = 0.0
        try:
            for v, w in [(x, 1) for x in vtx] + [(vgk, 2), (vck, 3)]:
                d = so_thuc_diem(v.get())
                if d is not None:
                    tong, tr = tong + d * w, tr + w
        except LoiNghiepVu:
            lb.config(text="?", foreground="#dc2626")
            return
        lb.config(text=f"{tong / tr:.2f}" if tr else "-", foreground=MAU_CHINH)

    def _doc_o_diem(self, lop) -> Dict[str, dict]:
        kq = {}
        for ma, o in self.o_diem.items():
            ten = self.ht.hoc_sinh[ma].ho_ten
            try:
                tx = [d for d in (so_thuc_diem(v.get()) for v in o["tx"]) if d is not None]
                kq[ma] = {"tx": tx, "gk": so_thuc_diem(o["gk"].get()), "ck": so_thuc_diem(o["ck"].get())}
            except LoiNghiepVu as e:
                raise LoiNghiepVu(f"{ten} ({ma}): {e}")
        return kq

    def luu_bang_diem(self) -> None:
        lop, mon, hk = self._chon_diem()
        if not (lop and mon and hk):
            return
        try:
            du_lieu = self._doc_o_diem(lop)
            n = self.ht.luu_bang_diem_lop(lop, mon, hk, du_lieu)
        except LoiNghiepVu as e:
            self.loi(e)
            return
        self.thanh_cong(f"Đã lưu bảng điểm {mon.ten_mon} - lớp {lop.ten_lop} ({n} học sinh).")
        self.nap_bang_diem()

    def xuat_bang_diem_csv(self) -> None:
        lop, mon, hk = self._chon_diem()
        if not (lop and mon and hk):
            return
        d = self.chon_noi_luu(f"bangdiem_{lop.ma_lop}_{mon.ma_mon}.csv", ".csv", "CSV")
        if not d:
            return
        hang = []
        for h in sorted(lop.danh_sach_hoc_sinh(), key=lambda x: (ten_cuoi(x.ho_ten), x.ma)):
            ds = [x for x in h.diem if x.mon_hoc is mon and x.hoc_ky is hk]
            tx = " ; ".join(f"{x.gia_tri:g}" for x in ds if x.loai_diem is LoaiDiem.THUONG_XUYEN)
            gk = next((f"{x.gia_tri:g}" for x in ds if x.loai_diem is LoaiDiem.GIUA_KY), "")
            ck = next((f"{x.gia_tri:g}" for x in ds if x.loai_diem is LoaiDiem.CUOI_KY), "")
            tb = h.diem_mon(mon, hk)
            hang.append([h.ma, h.ho_ten, tx, gk, ck, f"{tb:.2f}" if tb is not None else ""])
        ghi_csv(d, ["Mã HS", "Họ tên", "Thường xuyên", "Giữa kỳ", "Cuối kỳ", "TB môn"], hang)
        self.thanh_cong("Đã xuất: " + d)

    # ---------------------------------------------------------------- hạnh kiểm
    def nap_hanh_kiem(self) -> None:
        self._xoa_con(self.kv_hk)
        lop, _, hk = self._chon_diem()
        self.o_hk = {}
        if not (lop and hk):
            return
        gv = self.ht.tai_khoan_hien_tai.chu_so_huu
        duoc = self.ht.la_quan_tri() or lop.giao_vien_chu_nhiem is gv
        self.lb_hk_quyen.config(text="" if duoc else "Chỉ giáo viên chủ nhiệm mới được xếp loại hạnh kiểm (chế độ chỉ xem).")
        ngoai, trong = self.khung_cuon(self.kv_hk)
        ngoai.pack(fill="both", expand=True)
        for c, t in enumerate(["Mã", "Họ tên", "ĐTB", "Học lực", "Hạnh kiểm", "Nhận xét"]):
            ttk.Label(trong, text=t, style="Card.TLabel", font=(FONT, 10, "bold")).grid(row=0, column=c, padx=4, pady=4, sticky="w")
        for r, h in enumerate(sorted(lop.danh_sach_hoc_sinh(), key=lambda x: (ten_cuoi(x.ho_ten), x.ma)), 1):
            k = h.hanh_kiem_hoc_ky(hk)
            dtb = h.tinh_diem_trung_binh(hk)
            for c, t in enumerate([h.ma, h.ho_ten, f"{dtb:.2f}" if dtb else "-", xep_loai_hoc_luc(dtb) if dtb else "-"]):
                ttk.Label(trong, text=t, style="Card.TLabel").grid(row=r, column=c, padx=4, sticky="w")
            vxl, vnx = tk.StringVar(value=k.xep_loai.value if k else ""), tk.StringVar(value=k.nhan_xet if k else "")
            cb = ttk.Combobox(trong, textvariable=vxl, values=[""] + nhan_enum(XepLoaiHanhKiem), state="readonly", width=12)
            cb.grid(row=r, column=4, padx=4, pady=2)
            en = ttk.Entry(trong, textvariable=vnx, width=46)
            en.grid(row=r, column=5, padx=4, pady=2)
            if not duoc:
                cb.state(["disabled"])
                en.state(["disabled"])
            self.o_hk[h.ma] = (vxl, vnx)

    def luu_hanh_kiem(self) -> None:
        lop, _, hk = self._chon_diem()
        if not (lop and hk):
            return
        du_lieu = {ma: ((next((e for e in XepLoaiHanhKiem if e.value == vx.get()), None)), vn.get())
                   for ma, (vx, vn) in self.o_hk.items()}
        try:
            self.ht.luu_hanh_kiem_lop(lop, hk, du_lieu)
        except LoiNghiepVu as e:
            self.loi(e)
            return
        self.thanh_cong(f"Đã lưu hạnh kiểm lớp {lop.ten_lop} - {hk}.")
