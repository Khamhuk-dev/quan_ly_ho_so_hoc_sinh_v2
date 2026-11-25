# -*- coding: utf-8 -*-
"""Nền giao diện: kiểu dáng, bảng, hộp thoại biểu mẫu, biểu đồ, màn hình đăng nhập và khung chính."""
from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from ..config import PHIEN_BAN, TEN_UNG_DUNG, THU_MUC_XUAT
from ..enums import VaiTro
from ..models import GiaoVien, HocSinh, LopHoc
from ..utils import LoiNghiepVu, bo_dau, doc_ngay

MAU_CHINH, MAU_CHINH_DAM = "#2563eb", "#1d4ed8"
MAU_NEN, MAU_SIDEBAR, MAU_SIDEBAR_HOVER = "#f1f5f9", "#0f172a", "#1e293b"
MAU_NGUY_HIEM, MAU_CHU, MAU_PHU = "#dc2626", "#0f172a", "#64748b"
MAU_BIEU_DO = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2", "#db2777", "#65a30d"]
FONT = "Segoe UI"
CHUA_XEP_LOP = "(Chưa xếp lớp)"
TAT_CA = "Tất cả"


def nhan_enum(kieu) -> List[str]:
    return [e.value for e in kieu]


def enum_tu_nhan(kieu, nhan: str):
    for e in kieu:
        if e.value == nhan:
            return e
    raise LoiNghiepVu("Giá trị không hợp lệ: " + str(nhan))


class BienText:
    """Bọc tk.Text để dùng giống StringVar (get/set)."""

    def __init__(self, w: tk.Text, gia_tri: str = ""):
        self.w = w
        self.set(gia_tri)

    def get(self) -> str:
        return self.w.get("1.0", "end").strip()

    def set(self, v: str) -> None:
        self.w.delete("1.0", "end")
        self.w.insert("1.0", v)


class NenGUI:
    # ------------------------------------------------------------------
    # Kiểu dáng
    # ------------------------------------------------------------------
    def thiet_lap_kieu(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", font=(FONT, 10), background=MAU_NEN, foreground=MAU_CHU)
        s.configure("TFrame", background=MAU_NEN)
        s.configure("Card.TFrame", background="white")
        s.configure("TLabel", background=MAU_NEN)
        s.configure("Card.TLabel", background="white")
        s.configure("Muted.TLabel", background="white", foreground=MAU_PHU)
        s.configure("TEntry", padding=6, fieldbackground="white")
        s.configure("TCombobox", padding=5, fieldbackground="white")
        s.configure("TCheckbutton", background="white")
        s.configure("TNotebook", background=MAU_NEN, borderwidth=0)
        s.configure("TNotebook.Tab", padding=(14, 6), font=(FONT, 10))
        s.configure("Treeview", rowheight=28, background="white", fieldbackground="white", borderwidth=0)
        s.configure("Treeview.Heading", font=(FONT, 10, "bold"), background="#e2e8f0", padding=6, relief="flat")
        s.map("Treeview", background=[("selected", MAU_CHINH)], foreground=[("selected", "white")])
        s.configure("TButton", padding=(14, 7), background="#e2e8f0", borderwidth=0, focuscolor="none")
        s.map("TButton", background=[("active", "#cbd5e1")])
        s.configure("Primary.TButton", background=MAU_CHINH, foreground="white", font=(FONT, 10, "bold"))
        s.map("Primary.TButton", background=[("active", MAU_CHINH_DAM)])
        s.configure("Danger.TButton", background=MAU_NGUY_HIEM, foreground="white")
        s.map("Danger.TButton", background=[("active", "#b91c1c")])

    # ------------------------------------------------------------------
    # Tiện ích chung
    # ------------------------------------------------------------------
    def xoa_man_hinh(self) -> None:
        self._vung_cuon = []
        for w in self.winfo_children():
            w.destroy()

    def lam_moi(self) -> None:
        if self._lam_moi:
            self._lam_moi()

    def loi(self, e: Exception, cha=None) -> None:
        messagebox.showerror("Lỗi", str(e), parent=cha or self)

    def thanh_cong(self, noi_dung: str, cha=None) -> None:
        messagebox.showinfo("Thành công", noi_dung, parent=cha or self)

    def nut(self, cha, chu: str, lenh, kieu: str = "") -> ttk.Button:
        return ttk.Button(cha, text=chu, command=lenh, style=f"{kieu}.TButton" if kieu else "TButton")

    def the(self, cha, **kw) -> ttk.Frame:
        return ttk.Frame(cha, style="Card.TFrame", padding=kw.pop("padding", 18), **kw)

    def ds_lop_duoc_quan_ly(self) -> List[LopHoc]:
        return self.ht.ds_lop_duoc_quan_ly()

    def nhan_lop(self, l: LopHoc) -> str:
        return f"{l.ma_lop} - {l.ten_lop}"

    def lop_tu_nhan(self, s: str) -> Optional[LopHoc]:
        return self.ht.lop_hoc.get(s.split(" - ")[0].strip().upper()) if s else None

    def nhan_gv(self, g: GiaoVien) -> str:
        return f"{g.ma} - {g.ho_ten}"

    def nhan_hs(self, h: HocSinh) -> str:
        return f"{h.ma} - {h.ho_ten}"

    def hs_tu_nhan(self, s: str) -> Optional[HocSinh]:
        return self.ht.hoc_sinh.get(s.split(" - ")[0].strip().upper()) if s else None

    def hk_tu_nhan(self, s: str):
        return {str(h): h for h in self.ht.hoc_ky_tat_ca()}.get(s)

    def thu_muc_xuat(self) -> str:
        os.makedirs(THU_MUC_XUAT, exist_ok=True)
        return THU_MUC_XUAT

    def mo_tep(self, duong_dan: str) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(duong_dan)                                   # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", duong_dan])
            else:
                subprocess.Popen(["xdg-open", duong_dan])
        except Exception as e:                                           # noqa: BLE001
            messagebox.showwarning("Không mở được", f"Hãy tự mở:\n{duong_dan}\n\n({e})", parent=self)

    def chon_noi_luu(self, ten_goi_y: str, loai: str, mo_ta: str, cha=None) -> str:
        return filedialog.asksaveasfilename(parent=cha or self, defaultextension=loai, initialfile=ten_goi_y,
                                            initialdir=self.thu_muc_xuat(), filetypes=[(mo_ta, "*" + loai)])

    # ------------------------------------------------------------------
    # Bảng (Treeview) có sắp xếp khi bấm tiêu đề cột
    # ------------------------------------------------------------------
    def tao_bang(self, cha, cot: list, cao: int = 14) -> ttk.Treeview:
        """cot: [(id, tiêu đề, độ rộng[, căn lề])]"""
        khung = ttk.Frame(cha, style="Card.TFrame")
        khung.pack(fill="both", expand=True)
        cay = ttk.Treeview(khung, columns=[c[0] for c in cot], show="headings", height=cao, selectmode="browse")
        cay._tieu_de = {}
        cay._sx = (None, False)
        for c in cot:
            ma, tieu_de, rong = c[0], c[1], c[2]
            cay._tieu_de[ma] = tieu_de
            cay.heading(ma, text=tieu_de, command=lambda m=ma: self.bam_tieu_de(cay, m))
            cay.column(ma, width=rong, anchor=c[3] if len(c) > 3 else "w", minwidth=40)
        thanh = ttk.Scrollbar(khung, orient="vertical", command=cay.yview)
        cay.configure(yscrollcommand=thanh.set)
        cay.pack(side="left", fill="both", expand=True)
        thanh.pack(side="right", fill="y")
        cay.tag_configure("le", background="#f8fafc")
        cay.tag_configure("canh_bao", foreground=MAU_NGUY_HIEM)
        cay.tag_configure("mo", foreground="#94a3b8")
        return cay

    @staticmethod
    def _khoa_sap_xep(v: str):
        t = v.strip()
        try:
            return (0, float(t.replace(",", ".").rstrip("%")), "")
        except ValueError:
            pass
        try:
            return (1, doc_ngay(t).toordinal(), "")
        except ValueError:
            return (2, 0, bo_dau(t).lower())

    def bam_tieu_de(self, cay: ttk.Treeview, cot: str) -> None:
        hien = cay._sx
        dao = hien[0] == cot and not hien[1]
        self._sap_xep_bang(cay, cot, dao)

    def _sap_xep_bang(self, cay: ttk.Treeview, cot: str, dao: bool) -> None:
        ds = [(self._khoa_sap_xep(str(cay.set(i, cot))), i) for i in cay.get_children("")]
        ds.sort(key=lambda x: x[0], reverse=dao)
        for vt, (_, iid) in enumerate(ds):
            cay.move(iid, "", vt)
            tags = [t for t in cay.item(iid, "tags") if t != "le"]
            if vt % 2:
                tags.append("le")
            cay.item(iid, tags=tags)
        cay._sx = (cot, dao)
        for ma, tieu_de in cay._tieu_de.items():
            cay.heading(ma, text=tieu_de + (("  ▼" if dao else "  ▲") if ma == cot else ""))

    def do_bang(self, cay: ttk.Treeview, hang: list, tags_hang: Optional[dict] = None) -> None:
        """hang: [(iid, giá trị)]; tags_hang: {iid: 'canh_bao'...}"""
        cay.delete(*cay.get_children())
        for i, (iid, gia_tri) in enumerate(hang):
            tags = ["le"] if i % 2 else []
            if tags_hang and iid in tags_hang:
                tags.append(tags_hang[iid])
            cay.insert("", "end", iid=iid, values=gia_tri, tags=tuple(tags))
        cot, dao = cay._sx
        if cot is not None:
            self._sap_xep_bang(cay, cot, dao)

    def dong_chon(self, cay: ttk.Treeview) -> Optional[str]:
        sel = cay.selection()
        if not sel:
            messagebox.showinfo("Chưa chọn", "Hãy chọn một dòng trong bảng trước.", parent=self)
            return None
        return sel[0]

    def can_giua(self, top: tk.Toplevel) -> None:
        top.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - top.winfo_width()) // 2
        y = self.winfo_rooty() + max(20, (self.winfo_height() - top.winfo_height()) // 2)
        top.geometry(f"+{max(0, x)}+{max(0, y)}")

    # ------------------------------------------------------------------
    # Khung cuộn (lăn chuột hoạt động đúng chỗ, không rò sang trang khác)
    # ------------------------------------------------------------------
    def khung_cuon(self, cha, nen: str = "white"):
        ngoai = ttk.Frame(cha, style="Card.TFrame")
        cv = tk.Canvas(ngoai, bg=nen, highlightthickness=0)
        tb = ttk.Scrollbar(ngoai, orient="vertical", command=cv.yview)
        trong = ttk.Frame(cv, style="Card.TFrame", padding=12)
        cua_so = cv.create_window((0, 0), window=trong, anchor="nw")
        trong.bind("<Configure>", lambda _e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfigure(cua_so, width=e.width))
        cv.configure(yscrollcommand=tb.set)
        cv.pack(side="left", fill="both", expand=True)
        tb.pack(side="right", fill="y")
        self._vung_cuon.append(cv)
        return ngoai, trong

    def _cuon_chuot(self, e) -> None:
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except (KeyError, tk.TclError):
            return
        while w is not None:
            if isinstance(w, (ttk.Treeview, tk.Text)):
                return
            if w in self._vung_cuon:
                if getattr(e, "num", 0) == 4:
                    buoc = -3
                elif getattr(e, "num", 0) == 5:
                    buoc = 3
                else:
                    buoc = -3 if e.delta > 0 else 3
                w.yview_scroll(buoc, "units")
                return
            w = getattr(w, "master", None)

    # ------------------------------------------------------------------
    # Hộp thoại biểu mẫu
    # ------------------------------------------------------------------
    def hop_thoai_form(self, tieu_de: str, truong: list, luu, ban_dau: Optional[dict] = None,
                       nut_luu: str = "Lưu") -> tk.Toplevel:
        """truong: [{k, n, t: entry|pw|combo|check|text|sep, o: lựa chọn, d: vô hiệu hóa, v: mặc định}]
        Nếu phần tử đầu là 'sep' thì mỗi 'sep' là một tab."""
        ban_dau = ban_dau or {}
        top = tk.Toplevel(self)
        top.title(tieu_de)
        top.configure(bg="white")
        top.transient(self)
        top.resizable(False, False)
        khung = ttk.Frame(top, style="Card.TFrame", padding=22)
        khung.pack(fill="both", expand=True)
        ttk.Label(khung, text=tieu_de, style="Card.TLabel", font=(FONT, 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        dung_tab = bool(truong) and truong[0].get("t") == "sep"
        nb, cha, r, bien = None, khung, 1, {}
        if dung_tab:
            nb = ttk.Notebook(khung)
            nb.grid(row=1, column=0, columnspan=2, sticky="nsew")
        for f in truong:
            loai = f.get("t", "entry")
            if loai == "sep":
                if dung_tab:
                    cha = ttk.Frame(nb, style="Card.TFrame", padding=16)
                    nb.add(cha, text=f["n"])
                    r = 0
                else:
                    ttk.Label(cha, text=f["n"], style="Card.TLabel", font=(FONT, 10, "bold"),
                              foreground=MAU_CHINH).grid(row=r, column=0, columnspan=2, sticky="w", pady=(12, 4))
                    r += 1
                continue
            ttk.Label(cha, text=f["n"], style="Card.TLabel").grid(row=r, column=0, sticky="nw", pady=5, padx=(0, 16))
            gia_tri = ban_dau.get(f["k"], f.get("v", ""))
            if loai == "check":
                v = tk.BooleanVar(value=bool(gia_tri))
                w = ttk.Checkbutton(cha, variable=v)
            elif loai == "text":
                w = tk.Text(cha, width=40, height=3, wrap="word", font=(FONT, 10), relief="solid", bd=1)
                v = BienText(w, str(gia_tri))
            else:
                v = tk.StringVar(value=str(gia_tri))
                if loai == "combo":
                    w = ttk.Combobox(cha, textvariable=v, values=f["o"], state="readonly", width=34)
                else:
                    w = ttk.Entry(cha, textvariable=v, width=37, show="•" if loai == "pw" else "")
            if f.get("d"):
                if loai == "text":
                    w.configure(state="disabled")
                else:
                    w.state(["disabled"])
            w.grid(row=r, column=1, sticky="ew", pady=5)
            bien[f["k"]] = v
            r += 1
        hang_nut = 2 if dung_tab else r
        hn = ttk.Frame(khung, style="Card.TFrame")
        hn.grid(row=hang_nut, column=0, columnspan=2, sticky="e", pady=(16, 0))

        def bam() -> None:
            try:
                kq = luu({k: v.get() for k, v in bien.items()})
            except (LoiNghiepVu, ValueError) as e:
                self.loi(e, top)
                return
            if kq is not False:
                top.destroy()
                self.lam_moi()

        self.nut(hn, "Hủy", top.destroy).pack(side="left", padx=(0, 8))
        self.nut(hn, nut_luu, bam, "Primary").pack(side="left")
        top.bind("<Escape>", lambda _e: top.destroy())
        self.can_giua(top)
        try:
            top.wait_visibility()
            top.grab_set()
        except tk.TclError:
            pass
        return top

    # ------------------------------------------------------------------
    # Biểu đồ vẽ bằng Canvas (không cần thư viện ngoài)
    # ------------------------------------------------------------------
    def ve_cot(self, cv: tk.Canvas, tieu_de: str, nhan: list, gia_tri: list, mau: str = MAU_CHINH,
               toi_da: Optional[float] = None, dinh_dang=str) -> None:
        def ve(*_):
            cv.delete("all")
            w, h = max(cv.winfo_width(), 300), max(cv.winfo_height(), 120)
            cv.create_text(14, 14, anchor="w", text=tieu_de, font=(FONT, 10, "bold"), fill=MAU_CHU)
            if not nhan:
                return
            cao_nhat = toi_da or max(1, max(gia_tri))
            vung = (w - 40) / len(nhan)
            rong = min(60, vung * 0.62)
            day = h - 24
            tran = 40
            for i, (n, v) in enumerate(zip(nhan, gia_tri)):
                x = 20 + i * vung + (vung - rong) / 2
                cao = (day - tran) * (v / cao_nhat if cao_nhat else 0)
                cv.create_rectangle(x, day - cao, x + rong, day, fill=mau, outline="")
                cv.create_text(x + rong / 2, day - cao - 8, text=dinh_dang(v), font=(FONT, 9, "bold"), fill=MAU_CHU)
                cv.create_text(x + rong / 2, day + 12, text=n, font=(FONT, 9), fill=MAU_PHU)
        cv.bind("<Configure>", ve)
        ve()

    def ve_banh(self, cv: tk.Canvas, tieu_de: str, du_lieu: dict) -> None:
        def ve(*_):
            cv.delete("all")
            w, h = max(cv.winfo_width(), 300), max(cv.winfo_height(), 120)
            cv.create_text(14, 14, anchor="w", text=tieu_de, font=(FONT, 10, "bold"), fill=MAU_CHU)
            tong = sum(du_lieu.values())
            d = min(h - 44, 150)
            x0, y0 = 24, 32
            if not tong:
                cv.create_text(w / 2, h / 2, text="Chưa có dữ liệu", fill=MAU_PHU)
                return
            goc = 90.0
            for i, (k, v) in enumerate(du_lieu.items()):
                if v <= 0:
                    continue
                gd = 360.0 * v / tong
                cv.create_arc(x0, y0, x0 + d, y0 + d, start=goc, extent=-min(gd, 359.99),
                              fill=MAU_BIEU_DO[i % len(MAU_BIEU_DO)], outline="white", width=2)
                goc -= gd
            cv.create_oval(x0 + d * 0.3, y0 + d * 0.3, x0 + d * 0.7, y0 + d * 0.7, fill="white", outline="")
            cv.create_text(x0 + d / 2, y0 + d / 2, text=str(tong), font=(FONT, 14, "bold"), fill=MAU_CHU)
            for i, (k, v) in enumerate(du_lieu.items()):
                y = y0 + 8 + i * 26
                cv.create_rectangle(x0 + d + 24, y, x0 + d + 38, y + 14, fill=MAU_BIEU_DO[i % len(MAU_BIEU_DO)], outline="")
                cv.create_text(x0 + d + 46, y + 7, anchor="w", font=(FONT, 10), fill=MAU_CHU,
                               text=f"{k}: {v}  ({100 * v / tong:.0f}%)")
        cv.bind("<Configure>", ve)
        ve()

    # ------------------------------------------------------------------
    # Đăng nhập / đăng xuất
    # ------------------------------------------------------------------
    def hien_dang_nhap(self) -> None:
        self.xoa_man_hinh()
        self._lam_moi = None
        nen = tk.Frame(self, bg=MAU_SIDEBAR)
        nen.pack(fill="both", expand=True)
        the = tk.Frame(nen, bg="white", padx=44, pady=36)
        the.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(the, text="🎓", font=(FONT, 38), bg="white").pack()
        tk.Label(the, text="QUẢN LÝ HỒ SƠ HỌC SINH", font=(FONT, 16, "bold"), bg="white", fg=MAU_CHU).pack(pady=(4, 2))
        tk.Label(the, text="Đăng nhập để tiếp tục", bg="white", fg=MAU_PHU, font=(FONT, 10)).pack(pady=(0, 18))
        self.v_ten, self.v_mk = tk.StringVar(), tk.StringVar()
        for nhan, bien, an in (("Tên đăng nhập", self.v_ten, ""), ("Mật khẩu", self.v_mk, "•")):
            tk.Label(the, text=nhan, bg="white", fg=MAU_PHU, anchor="w").pack(fill="x")
            e = ttk.Entry(the, textvariable=bien, width=34, show=an)
            e.pack(pady=(2, 12), ipady=3)
            e.bind("<Return>", lambda _e: self.xu_ly_dang_nhap())
            if not an:
                e.focus_set()
        self.lb_loi = tk.Label(the, text="", fg=MAU_NGUY_HIEM, bg="white", wraplength=300, justify="left")
        self.lb_loi.pack(fill="x")
        ttk.Button(the, text="Đăng nhập", style="Primary.TButton", command=self.xu_ly_dang_nhap).pack(
            fill="x", pady=(8, 0))
        if self.ht.mat_khau_mac_dinh_con_dung():
            tk.Label(the, text="Tài khoản mẫu: admin/admin123 · gv01/gv123 · hs001/hs123 · ph001/ph123\n"
                               "(hãy đổi mật khẩu sau khi đăng nhập)", bg="white", fg="#94a3b8", font=(FONT, 8),
                     wraplength=330).pack(pady=(16, 0))
        tk.Label(nen, text=f"{TEN_UNG_DUNG} · phiên bản {PHIEN_BAN} · Dữ liệu: {self.ht.duong_dan_db}",
                 bg=MAU_SIDEBAR, fg="#64748b", font=(FONT, 8)).pack(side="bottom", pady=8)

    def xu_ly_dang_nhap(self) -> None:
        ten, mk = self.v_ten.get().strip(), self.v_mk.get()
        if not ten or not mk:
            self.lb_loi.config(text="Vui lòng nhập đủ tên đăng nhập và mật khẩu.")
            return
        try:
            self.ht.dang_nhap(ten, mk)
        except LoiNghiepVu as e:
            self.lb_loi.config(text=str(e))
            self.v_mk.set("")
            return
        self.hien_chinh()

    def dang_xuat(self) -> None:
        self.ht.dang_xuat()
        self.hien_dang_nhap()

    def thoat(self) -> None:
        """Đóng cửa sổ: lưu lần cuối rồi đóng kết nối cơ sở dữ liệu."""
        try:
            self.ht.luu_du_lieu()
            self.ht.dong()
        finally:
            self.destroy()

    # ------------------------------------------------------------------
    # Khung chính + menu theo vai trò
    # ------------------------------------------------------------------
    def cap_nhat_trang_thai(self) -> None:
        try:
            moi = self.ht.lan_luu_cuoi
            self.lb_trang_thai.config(
                text=f"💾  Dữ liệu tự động lưu tại: {self.ht.duong_dan_db}" +
                     (f"    ·    Lưu lần cuối: {moi:%H:%M:%S}" if moi else ""))
        except (tk.TclError, AttributeError):
            pass

    def hien_chinh(self) -> None:
        self.xoa_man_hinh()
        tk_ = self.ht.tai_khoan_hien_tai
        vt = tk_.vai_tro
        dau = tk.Frame(self, bg="white", height=56)
        dau.pack(fill="x")
        dau.pack_propagate(False)
        tk.Label(dau, text="🎓  Quản lý hồ sơ học sinh", font=(FONT, 13, "bold"), bg="white", fg=MAU_CHU).pack(
            side="left", padx=20)
        ttk.Button(dau, text="Đăng xuất", command=self.dang_xuat).pack(side="right", padx=16)
        tk.Label(dau, text=f"{tk_.chu_so_huu.ho_ten}  ·  {vt.value}", bg="white", fg=MAU_PHU).pack(side="right")
        chan = tk.Frame(self, bg="#e2e8f0", height=26)
        chan.pack(side="bottom", fill="x")
        chan.pack_propagate(False)
        self.lb_trang_thai = tk.Label(chan, bg="#e2e8f0", fg=MAU_PHU, font=(FONT, 8), anchor="w")
        self.lb_trang_thai.pack(fill="x", padx=12)
        self.ht.khi_luu = self.cap_nhat_trang_thai
        self.cap_nhat_trang_thai()
        than = tk.Frame(self, bg=MAU_NEN)
        than.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(than, bg=MAU_SIDEBAR, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.vung = tk.Frame(than, bg=MAU_NEN)
        self.vung.pack(side="left", fill="both", expand=True, padx=24, pady=16)

        if vt in (VaiTro.HOC_SINH, VaiTro.PHU_HUYNH):
            muc = [("👤  Thông tin cá nhân", self.trang_thong_tin_ca_nhan),
                   ("📊  Điểm và học lực", self.trang_xem_diem),
                   ("🗓  Điểm danh", self.trang_xem_diem_danh)]
        else:
            muc = [("🏠  Tổng quan", self.trang_tong_quan),
                   ("📋  Hồ sơ học sinh", self.trang_hoc_sinh),
                   ("📝  Nhập điểm / hạnh kiểm", self.trang_diem),
                   ("✅  Điểm danh", self.trang_diem_danh),
                   ("📈  Thống kê, báo cáo", self.trang_thong_ke)]
            if vt is VaiTro.QUAN_TRI:
                muc += [("🏫  Quản lý lớp học", self.trang_lop_hoc),
                        ("📚  Quản lý môn học", self.trang_mon_hoc),
                        ("👩‍🏫  Quản lý giáo viên", self.trang_giao_vien),
                        ("📅  Năm học, học kỳ", self.trang_nam_hoc),
                        ("🔑  Quản lý tài khoản", self.trang_tai_khoan),
                        ("⚙  Hệ thống, sao lưu", self.trang_he_thong)]
        self.nut_menu = {}
        for ten, ham in muc:
            b = tk.Button(self.sidebar, text=ten, anchor="w", bg=MAU_SIDEBAR, fg="#e2e8f0", bd=0, relief="flat",
                          activebackground=MAU_SIDEBAR_HOVER, activeforeground="white", padx=20, pady=9,
                          font=(FONT, 11), cursor="hand2", highlightthickness=0,
                          command=lambda t=ten, h=ham: self.mo_trang(t, h))
            b.pack(fill="x")
            b.bind("<Enter>", lambda _e, w=b: w["bg"] != MAU_CHINH and w.config(bg=MAU_SIDEBAR_HOVER))
            b.bind("<Leave>", lambda _e, w=b: w["bg"] != MAU_CHINH and w.config(bg=MAU_SIDEBAR))
            self.nut_menu[ten] = b
        tk.Button(self.sidebar, text="🔒  Đổi mật khẩu", anchor="w", bg=MAU_SIDEBAR, fg="#94a3b8", bd=0, relief="flat",
                  activebackground=MAU_SIDEBAR_HOVER, activeforeground="white", padx=20, pady=10, font=(FONT, 10),
                  cursor="hand2", highlightthickness=0, command=self.hop_thoai_doi_mat_khau).pack(
            side="bottom", fill="x", pady=8)
        self.mo_trang(*muc[0])

    def mo_trang(self, ten: str, ham) -> None:
        for t, b in self.nut_menu.items():
            b.config(bg=MAU_CHINH if t == ten else MAU_SIDEBAR, fg="white" if t == ten else "#e2e8f0")
        for w in self.vung.winfo_children():
            w.destroy()
        self._vung_cuon = []
        self._lam_moi = None
        tk.Label(self.vung, text=ten.split("  ", 1)[1], font=(FONT, 20, "bold"), bg=MAU_NEN, fg=MAU_CHU,
                 anchor="w").pack(fill="x", pady=(0, 10))
        noi_dung = tk.Frame(self.vung, bg=MAU_NEN)
        noi_dung.pack(fill="both", expand=True)
        ham(noi_dung)

    def hop_thoai_doi_mat_khau(self) -> None:
        def luu(v: dict):
            if v["moi"] != v["nhap_lai"]:
                raise LoiNghiepVu("Mật khẩu nhập lại không khớp.")
            self.ht.doi_mat_khau(v["cu"], v["moi"])
            self.thanh_cong("Đã đổi mật khẩu.")

        self.hop_thoai_form("Đổi mật khẩu", [
            {"k": "cu", "n": "Mật khẩu hiện tại", "t": "pw"},
            {"k": "moi", "n": "Mật khẩu mới (≥ 6 ký tự)", "t": "pw"},
            {"k": "nhap_lai", "n": "Nhập lại mật khẩu mới", "t": "pw"}], luu, nut_luu="Đổi mật khẩu")

    # ------------------------------------------------------------------
    # Bộ chọn dùng chung cho các trang
    # ------------------------------------------------------------------
    def thanh_chon(self, cha, nhan: str, bien: tk.StringVar, gia_tri: list, rong: int = 18, khi_chon=None) -> ttk.Combobox:
        ttk.Label(cha, text=nhan).pack(side="left")
        cb = ttk.Combobox(cha, textvariable=bien, values=gia_tri, state="readonly", width=rong)
        cb.pack(side="left", padx=(6, 16))
        if khi_chon:
            cb.bind("<<ComboboxSelected>>", lambda _e: khi_chon())
        return cb
