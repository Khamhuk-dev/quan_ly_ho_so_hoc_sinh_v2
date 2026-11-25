# -*- coding: utf-8 -*-
"""Trang Hồ sơ học sinh + các khối giao diện dùng lại cho trang Học sinh/Phụ huynh."""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from ..enums import GioiTinh, TrangThaiDiemDanh, TrangThaiHocSinh
from ..exporters import xuat_html_ho_so
from ..models import HocSinh, PhuHuynh
from ..utils import LoiNghiepVu, chuoi_ngay, dinh_dang_dtb, ngay_hop_le, xep_loai_hoc_luc
from .nen import (CHUA_XEP_LOP, FONT, MAU_CHINH, MAU_NEN, MAU_PHU, TAT_CA, enum_tu_nhan, nhan_enum)

THU = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
QUAN_HE = ["Bố", "Mẹ", "Ông", "Bà", "Anh/Chị", "Người giám hộ"]


class TrangHocSinh:
    # ================================================================== khối dùng lại
    def dong_thong_tin(self, hs: HocSinh) -> list:
        lop, r = hs.lop_hien_tai, hs.ho_so
        kq = [("Mã học sinh", hs.ma_hoc_sinh), ("Họ tên", hs.ho_ten),
              ("Ngày sinh", f"{chuoi_ngay(hs.ngay_sinh)}  ({hs.tinh_tuoi()} tuổi)"),
              ("Giới tính", hs.gioi_tinh.value), ("Nơi sinh", hs.noi_sinh), ("Dân tộc", hs.dan_toc),
              ("CMND/CCCD", hs.so_cccd), ("Địa chỉ", hs.dia_chi), ("Điện thoại", hs.so_dien_thoai),
              ("Email", hs.email), ("Lớp", lop.ten_lop if lop else CHUA_XEP_LOP),
              ("GVCN", lop.giao_vien_chu_nhiem.ho_ten if lop and lop.giao_vien_chu_nhiem else "-"),
              ("Trạng thái", hs.trang_thai.value), ("Ngày nhập học", chuoi_ngay(hs.ngay_nhap_hoc)),
              ("Mã hồ sơ", r.ma_ho_so), ("Sức khỏe", r.ghi_chu_suc_khoe), ("Thành tích", r.thanh_tich),
              ("Kỷ luật", r.ghi_chu_ky_luat)]
        kq += [(f"Phụ huynh ({p.quan_he})", f"{p.ho_ten} · {p.so_dien_thoai} · {p.nghe_nghiep}") for p in hs.phu_huynh]
        return kq

    def dung_the_thong_tin(self, cha, hs: HocSinh) -> None:
        for i, (k, v) in enumerate(self.dong_thong_tin(hs)):
            ttk.Label(cha, text=k, style="Muted.TLabel").grid(row=i, column=0, sticky="nw", pady=3, padx=(0, 24))
            ttk.Label(cha, text=v or "—", style="Card.TLabel", wraplength=480, justify="left").grid(
                row=i, column=1, sticky="w", pady=3)

    def dung_bang_diem(self, cha, lay_hs):
        ht = self.ht
        v_hk = tk.StringVar()
        hk0 = ht.hoc_ky_hien_tai()
        v_hk.set(str(hk0) if hk0 else "")
        hang = tk.Frame(cha, bg="white")
        hang.pack(fill="x", pady=(0, 8))
        ttk.Label(hang, text="Học kỳ:", style="Card.TLabel").pack(side="left")
        cb = ttk.Combobox(hang, textvariable=v_hk, values=[str(h) for h in ht.hoc_ky_tat_ca()], state="readonly", width=24)
        cb.pack(side="left", padx=8)
        bang = self.tao_bang(cha, [("mon", "Môn", 150), ("tx", "Thường xuyên", 170), ("gk", "Giữa kỳ", 80),
                                   ("ck", "Cuối kỳ", 80), ("tb", "TB môn", 80)], cao=12)
        lb = tk.Label(cha, bg="white", fg=MAU_CHINH, font=(FONT, 11, "bold"), anchor="w", justify="left")
        lb.pack(fill="x", pady=(8, 0))

        def nap(*_):
            hs, hk = lay_hs(), self.hk_tu_nhan(v_hk.get())
            self.do_bang(bang, [])
            lb.config(text="")
            if not (hs and hk):
                return
            hang_ = []
            for m in sorted({d.mon_hoc for d in hs.diem if d.hoc_ky is hk}, key=lambda m: m.ma_mon):
                lay = lambda loai: ", ".join(f"{d.gia_tri:g}" for d in hs.diem
                                             if d.mon_hoc is m and d.hoc_ky is hk and d.loai_diem.name == loai) or "-"
                hang_.append((m.ma_mon, (m.ten_mon, lay("THUONG_XUYEN"), lay("GIUA_KY"), lay("CUOI_KY"),
                                         f"{hs.diem_mon(m, hk):.2f}")))
            self.do_bang(bang, hang_)
            dtb, hkq = hs.tinh_diem_trung_binh(hk), hs.hanh_kiem_hoc_ky(hk)
            lb.config(text=(f"Điểm trung bình: {dtb:.2f}  ·  Học lực: {xep_loai_hoc_luc(dtb)}" if dtb else "Chưa có điểm")
                      + "  ·  Hạnh kiểm: " + (hkq.xep_loai.value if hkq else "chưa xếp loại"))
        cb.bind("<<ComboboxSelected>>", nap)
        nap()
        return nap

    def dung_diem_danh_hs(self, cha, lay_hs):
        lb = tk.Label(cha, bg="white", fg=MAU_CHINH, font=(FONT, 10, "bold"), anchor="w", justify="left")
        lb.pack(fill="x", pady=(0, 6))
        v_chi = tk.BooleanVar(value=False)
        bang = None

        def nap(*_):
            hs = lay_hs()
            if hs is None:
                return
            t = hs.thong_ke_diem_danh()
            tong = sum(t.values())
            cc = f"  ·  Chuyên cần: {100 * (t[TrangThaiDiemDanh.CO_MAT] + t[TrangThaiDiemDanh.DI_MUON]) / tong:.1f}%" if tong else ""
            lb.config(text="  ·  ".join(f"{k.value}: {v}" for k, v in t.items()) + cc)
            ds = sorted(hs.diem_danh, key=lambda d: d.ngay, reverse=True)
            if v_chi.get():
                ds = [d for d in ds if d.trang_thai is not TrangThaiDiemDanh.CO_MAT]
            self.do_bang(bang, [(str(i), (chuoi_ngay(d.ngay), THU[d.ngay.weekday()], d.lop_hoc.ten_lop, d.trang_thai.value,
                                          d.ghi_chu)) for i, d in enumerate(ds[:200])],
                         {str(i): "canh_bao" for i, d in enumerate(ds[:200])
                          if d.trang_thai is TrangThaiDiemDanh.VANG_KHONG_PHEP})
        ttk.Checkbutton(cha, text="Chỉ hiện ngày vắng / đi muộn", variable=v_chi, command=nap).pack(anchor="w")
        bang = self.tao_bang(cha, [("ngay", "Ngày", 100), ("thu", "Thứ", 70), ("lop", "Lớp", 70),
                                   ("tt", "Trạng thái", 130), ("gc", "Ghi chú", 220)], cao=11)
        nap()
        return nap

    def dung_chi_tiet_hs(self, cha, hs: HocSinh) -> ttk.Notebook:
        nb = ttk.Notebook(cha)
        nb.pack(fill="both", expand=True)
        t1 = ttk.Frame(nb, style="Card.TFrame")
        ngoai, trong = self.khung_cuon(t1)
        ngoai.pack(fill="both", expand=True)
        self.dung_the_thong_tin(trong, hs)
        nb.add(t1, text="Thông tin")
        t2 = ttk.Frame(nb, style="Card.TFrame", padding=10)
        self.dung_bang_diem(t2, lambda: hs)
        nb.add(t2, text="Kết quả học tập")
        t3 = ttk.Frame(nb, style="Card.TFrame", padding=10)
        self.dung_diem_danh_hs(t3, lambda: hs)
        nb.add(t3, text="Điểm danh")
        t4 = ttk.Frame(nb, style="Card.TFrame", padding=10)
        ttk.Label(t4, text="Lịch sử lớp", style="Card.TLabel", font=(FONT, 10, "bold")).pack(anchor="w")
        b1 = self.tao_bang(t4, [("lop", "Lớp", 100), ("vao", "Từ ngày", 110), ("ra", "Đến ngày", 110)], cao=4)
        self.do_bang(b1, [(str(i), (g.lop_hoc.ten_lop, chuoi_ngay(g.ngay_vao), chuoi_ngay(g.ngay_ra) or "nay"))
                          for i, g in enumerate(hs.ghi_danh)])
        ttk.Label(t4, text="Hạnh kiểm", style="Card.TLabel", font=(FONT, 10, "bold")).pack(anchor="w", pady=(10, 0))
        b2 = self.tao_bang(t4, [("hk", "Học kỳ", 150), ("xl", "Xếp loại", 100), ("nx", "Nhận xét", 320)], cao=4)
        self.do_bang(b2, [(str(i), (str(k.hoc_ky), k.xep_loai.value, k.nhan_xet))
                          for i, k in enumerate(hs.ket_qua_hanh_kiem)])
        nb.add(t4, text="Lịch sử & hạnh kiểm")
        return nb

    # ================================================================== trang chính
    def trang_hoc_sinh(self, p) -> None:
        ht = self.ht
        tren = tk.Frame(p, bg=MAU_NEN)
        tren.pack(fill="x", pady=(0, 8))
        self.v_kw, self.v_lop_loc = tk.StringVar(), tk.StringVar(value=TAT_CA)
        self.v_tt_loc, self.v_sx = tk.StringVar(value=TAT_CA), tk.StringVar(value="Mã")
        ttk.Label(tren, text="Tìm kiếm (mã/họ tên/SĐT):").pack(side="left")
        ttk.Entry(tren, textvariable=self.v_kw, width=20).pack(side="left", padx=(6, 12))
        lops = [TAT_CA, CHUA_XEP_LOP] + [self.nhan_lop(l) for l in sorted(ht.lop_hoc.values(), key=lambda x: x.ma_lop)]
        self.thanh_chon(tren, "Lớp:", self.v_lop_loc, lops, 13)
        self.thanh_chon(tren, "Trạng thái:", self.v_tt_loc, [TAT_CA] + nhan_enum(TrangThaiHocSinh), 12)
        self.thanh_chon(tren, "Sắp xếp:", self.v_sx, ["Mã", "Tên", "Ngày sinh", "Lớp"], 9)
        for v in (self.v_kw, self.v_lop_loc, self.v_tt_loc, self.v_sx):
            v.trace_add("write", lambda *_: self.nap_ds_hs())
        nut = tk.Frame(p, bg=MAU_NEN)
        nut.pack(fill="x", pady=(0, 8))
        self.nut(nut, "＋ Thêm hồ sơ", lambda: self.form_hoc_sinh(None), "Primary").pack(side="left", padx=(0, 8))
        self.nut(nut, "Xem chi tiết", self.xem_chi_tiet).pack(side="left", padx=(0, 8))
        self.nut(nut, "Sửa", self.sua_hoc_sinh).pack(side="left", padx=(0, 8))
        self.nut(nut, "Chuyển lớp", self.chuyen_lop_gui).pack(side="left", padx=(0, 8))
        self.nut(nut, "Xóa", self.xoa_hoc_sinh, "Danger").pack(side="left", padx=(0, 8))
        mb = ttk.Menubutton(nut, text="Tiện ích ▾")
        menu = tk.Menu(mb, tearoff=0)
        for ten, ham in (("Nhập học sinh từ CSV…", self.nhap_csv_gui), ("Tải tệp CSV mẫu…", self.csv_mau_gui),
                         ("Xuất danh sách ra CSV…", self.xuat_csv_gui), ("In hồ sơ (mở trình duyệt)", self.in_ho_so),
                         ("Xuất hồ sơ PDF…", self.xuat_pdf_gui)):
            menu.add_command(label=ten, command=ham)
        mb["menu"] = menu
        mb.pack(side="right")
        the = self.the(p, padding=8)
        the.pack(fill="both", expand=True)
        self.bang_hs = self.tao_bang(the, [("ma", "Mã", 70), ("ten", "Họ tên", 190), ("ns", "Ngày sinh", 95),
                                           ("gt", "Giới tính", 70), ("lop", "Lớp", 60), ("tt", "Trạng thái", 100),
                                           ("sdt", "Điện thoại", 105), ("dtb", "ĐTB", 60, "e")])
        self.bang_hs.bind("<Double-1>", lambda _e: self.xem_chi_tiet())
        self.lb_tong = tk.Label(p, bg=MAU_NEN, fg=MAU_PHU, anchor="w")
        self.lb_tong.pack(fill="x", pady=(6, 0))
        self._lam_moi = self.nap_ds_hs
        self.nap_ds_hs()

    def nap_ds_hs(self) -> None:
        ht = self.ht
        khoa = {"Mã": "ma", "Tên": "ten", "Ngày sinh": "ngaysinh", "Lớp": "lop"}[self.v_sx.get()]
        ds = ht.danh_sach(khoa)
        kw = self.v_kw.get().strip()
        if kw:
            ma = {h.ma for h in ht.tim_kiem(kw)}
            ds = [h for h in ds if h.ma in ma]
        loc = self.v_lop_loc.get()
        if loc == CHUA_XEP_LOP:
            ds = [h for h in ds if h.lop_hien_tai is None]
        elif loc != TAT_CA:
            lop = self.lop_tu_nhan(loc)
            ds = [h for h in ds if h.lop_hien_tai is lop]
        if self.v_tt_loc.get() != TAT_CA:
            tt = enum_tu_nhan(TrangThaiHocSinh, self.v_tt_loc.get())
            ds = [h for h in ds if h.trang_thai is tt]
        self.ds_dang_hien = ds
        hk = ht.hoc_ky_hien_tai()
        self.do_bang(self.bang_hs, [(h.ma, (h.ma, h.ho_ten, chuoi_ngay(h.ngay_sinh), h.gioi_tinh.value,
                                            h.lop_hien_tai.ten_lop if h.lop_hien_tai else "-", h.trang_thai.value,
                                            h.so_dien_thoai, dinh_dang_dtb(h.tinh_diem_trung_binh(hk) if hk else 0)))
                                    for h in ds],
                     {h.ma: "mo" for h in ds if h.trang_thai is not TrangThaiHocSinh.DANG_HOC})
        self.lb_tong.config(text=f"Hiển thị {len(ds)} / {len(ht.hoc_sinh)} học sinh")

    def hs_dang_chon(self) -> Optional[HocSinh]:
        iid = self.dong_chon(self.bang_hs)
        return self.ht.hoc_sinh.get(iid) if iid else None

    def xem_chi_tiet(self) -> None:
        hs = self.hs_dang_chon()
        if hs is None:
            return
        top = tk.Toplevel(self)
        top.title("Chi tiết hồ sơ")
        top.configure(bg="white")
        top.transient(self)
        top.geometry("760x620")
        khung = ttk.Frame(top, style="Card.TFrame", padding=20)
        khung.pack(fill="both", expand=True)
        ttk.Label(khung, text=f"Hồ sơ: {hs.ho_ten}  ({hs.ma})", style="Card.TLabel", font=(FONT, 15, "bold")).pack(anchor="w", pady=(0, 8))
        hn = ttk.Frame(khung, style="Card.TFrame")
        hn.pack(side="bottom", anchor="e", pady=(10, 0))
        self.nut(hn, "In hồ sơ", lambda: self.in_ho_so(hs)).pack(side="left", padx=8)
        self.nut(hn, "Xuất PDF", lambda: self.xuat_pdf_gui(hs, top)).pack(side="left", padx=8)
        self.nut(hn, "Đóng", top.destroy, "Primary").pack(side="left")
        self.dung_chi_tiet_hs(khung, hs)
        self.can_giua(top)

    def in_ho_so(self, hs: Optional[HocSinh] = None) -> None:
        hs = hs if isinstance(hs, HocSinh) else self.hs_dang_chon()
        if hs is None:
            return
        d = os.path.join(self.thu_muc_xuat(), f"hoso_{hs.ma}.html")
        self.mo_tep(xuat_html_ho_so(hs, d, self.ht.hoc_ky_hien_tai()))

    def xuat_pdf_gui(self, hs=None, cha=None) -> None:
        hs = hs if isinstance(hs, HocSinh) else self.hs_dang_chon()
        if hs is None:
            return
        d = self.chon_noi_luu(f"hoso_{hs.ma}.pdf", ".pdf", "PDF", cha)
        if d:
            self.thanh_cong("Đã xuất: " + hs.ho_so.xuat_pdf(d) + "\n(PDF bỏ dấu; dùng 'In hồ sơ' để có đủ dấu tiếng Việt)", cha)

    # ---------------------------------------------------------------- thêm / sửa / xóa / chuyển lớp
    def sua_hoc_sinh(self) -> None:
        hs = self.hs_dang_chon()
        if hs is None:
            return
        if not self.ht.co_quyen_sua(hs):
            messagebox.showwarning("Không có quyền", "Bạn chỉ được sửa học sinh thuộc lớp mình phụ trách.", parent=self)
            return
        self.form_hoc_sinh(hs)

    def form_hoc_sinh(self, hs: Optional[HocSinh]) -> None:
        ht = self.ht
        ds_lop = ([CHUA_XEP_LOP] if ht.la_quan_tri() else []) + [self.nhan_lop(l) for l in self.ds_lop_duoc_quan_ly()]
        if len(ds_lop) == 0:
            messagebox.showwarning("Không có quyền", "Bạn chưa phụ trách lớp nào nên không thể thêm học sinh.", parent=self)
            return
        sua = hs is not None
        if sua:
            r = hs.ho_so
            bd = {"ma": hs.ma, "ho_ten": hs.ho_ten, "ngay_sinh": chuoi_ngay(hs.ngay_sinh), "gioi_tinh": hs.gioi_tinh.value,
                  "noi_sinh": hs.noi_sinh, "dan_toc": hs.dan_toc, "cccd": hs.so_cccd, "dia_chi": hs.dia_chi,
                  "sdt": hs.so_dien_thoai, "email": hs.email,
                  "lop": self.nhan_lop(hs.lop_hien_tai) if hs.lop_hien_tai else CHUA_XEP_LOP,
                  "trang_thai": hs.trang_thai.value, "ngay_nhap_hoc": chuoi_ngay(hs.ngay_nhap_hoc),
                  "suc_khoe": r.ghi_chu_suc_khoe, "thanh_tich": r.thanh_tich, "ky_luat": r.ghi_chu_ky_luat}
            for i, ph in enumerate(hs.phu_huynh[:2], 1):
                bd.update({f"ph{i}_ten": ph.ho_ten, f"ph{i}_ngay": chuoi_ngay(ph.ngay_sinh), f"ph{i}_quan_he": ph.quan_he,
                           f"ph{i}_nghe": ph.nghe_nghiep, f"ph{i}_sdt": ph.so_dien_thoai, f"ph{i}_email": ph.email})
        else:
            bd = {"ma": ht.ma_tiep_theo("HS"), "gioi_tinh": "Nam", "trang_thai": "Đang học", "dan_toc": "Kinh",
                  "lop": ds_lop[0] if ds_lop[0] != CHUA_XEP_LOP or len(ds_lop) == 1 else ds_lop[1],
                  "ph1_quan_he": "Bố", "ph2_quan_he": "Mẹ", "tao_tk_hs": True}

        def luu(v: dict):
            ma = v["ma"].strip().upper()
            if not sua and ht.kiem_tra_ma_trung(ma):
                raise LoiNghiepVu(f"Mã {ma} đã tồn tại.")
            tt = enum_tu_nhan(TrangThaiHocSinh, v["trang_thai"])
            moi = HocSinh(ma, v["ho_ten"], ngay_hop_le(v["ngay_sinh"], "Ngày sinh"), enum_tu_nhan(GioiTinh, v["gioi_tinh"]),
                          v["dia_chi"], v["sdt"], v["email"], ngay_hop_le(v["ngay_nhap_hoc"], "Ngày nhập học", False),
                          tt, v["noi_sinh"], v["dan_toc"], v["cccd"])
            thong_tin = []
            for i in (1, 2):
                t = {"ho_ten": v[f"ph{i}_ten"], "ngay_sinh": ngay_hop_le(v[f"ph{i}_ngay"], f"Ngày sinh phụ huynh {i}", False),
                     "quan_he": v[f"ph{i}_quan_he"], "nghe": v[f"ph{i}_nghe"], "sdt": v[f"ph{i}_sdt"],
                     "email": v[f"ph{i}_email"], "dia_chi": v["dia_chi"]}
                if t["ho_ten"].strip():
                    PhuHuynh("TAM", t["ho_ten"], t["ngay_sinh"], GioiTinh.KHAC, "", t["sdt"], t["email"])   # chỉ để kiểm tra hợp lệ
                thong_tin.append(t)
            lop = self.lop_tu_nhan(v["lop"])
            if not sua and lop is None and not ht.la_quan_tri():
                raise LoiNghiepVu("Giáo viên cần chọn một lớp mình phụ trách.")
            if sua:
                ht.sua_ho_so_hoc_sinh(hs, moi, lop, tt, v["suc_khoe"], v["thanh_tich"], v["ky_luat"],
                                      moi.ngay_nhap_hoc if v["ngay_nhap_hoc"].strip() else None)
                ht.cap_nhat_phu_huynh_cua_hs(hs, thong_tin, v.get("tao_tk_ph", False))
            else:
                if tt is not TrangThaiHocSinh.DANG_HOC and lop is not None:
                    raise LoiNghiepVu("Chỉ học sinh 'Đang học' mới được xếp vào lớp.")
                moi.trang_thai = tt
                moi.ho_so.cap_nhat_ho_so(v["suc_khoe"], v["thanh_tich"], v["ky_luat"])
                tk_moi = ht.them_ho_so_hoc_sinh(moi, lop, ht.tao_phu_huynh_moi(thong_tin),
                                                v.get("tao_tk_hs", False), v.get("tao_tk_ph", False))
                if tk_moi:
                    messagebox.showinfo("Đã tạo tài khoản", "Tài khoản đăng nhập mới:\n" + "\n".join(
                        f"  {t}  /  {m}" for t, m in tk_moi) + "\n\nHãy yêu cầu đổi mật khẩu sau lần đăng nhập đầu.", parent=self)

        def ph_tab(i):
            return [{"t": "sep", "n": f"Phụ huynh {i}"}] if False else [
                {"k": f"ph{i}_ten", "n": "Họ tên"}, {"k": f"ph{i}_quan_he", "n": "Quan hệ", "t": "combo", "o": QUAN_HE},
                {"k": f"ph{i}_ngay", "n": "Ngày sinh (dd/mm/yyyy)"}, {"k": f"ph{i}_nghe", "n": "Nghề nghiệp"},
                {"k": f"ph{i}_sdt", "n": "Số điện thoại"}, {"k": f"ph{i}_email", "n": "Email"}]
        truong = [
            {"t": "sep", "n": "Thông tin cá nhân"},
            {"k": "ma", "n": "Mã học sinh *", "d": sua}, {"k": "ho_ten", "n": "Họ tên *"},
            {"k": "ngay_sinh", "n": "Ngày sinh * (dd/mm/yyyy)"},
            {"k": "gioi_tinh", "n": "Giới tính", "t": "combo", "o": nhan_enum(GioiTinh)},
            {"k": "noi_sinh", "n": "Nơi sinh"}, {"k": "dan_toc", "n": "Dân tộc"}, {"k": "cccd", "n": "CMND/CCCD"},
            {"k": "dia_chi", "n": "Địa chỉ"}, {"k": "sdt", "n": "Số điện thoại"}, {"k": "email", "n": "Email"},
            {"t": "sep", "n": "Lớp & hồ sơ"},
            {"k": "lop", "n": "Lớp", "t": "combo", "o": ds_lop},
            {"k": "trang_thai", "n": "Trạng thái", "t": "combo", "o": nhan_enum(TrangThaiHocSinh)},
            {"k": "ngay_nhap_hoc", "n": "Ngày nhập học (dd/mm/yyyy)"},
            {"k": "suc_khoe", "n": "Ghi chú sức khỏe", "t": "text"}, {"k": "thanh_tich", "n": "Thành tích", "t": "text"},
            {"k": "ky_luat", "n": "Ghi chú kỷ luật", "t": "text"},
            {"t": "sep", "n": "Phụ huynh 1"}] + ph_tab(1) + [{"t": "sep", "n": "Phụ huynh 2"}] + ph_tab(2) + [
            {"t": "sep", "n": "Tài khoản"},
            {"k": "tao_tk_hs", "n": f"Tạo TK học sinh (mật khẩu 123456)", "t": "check", "d": sua},
            {"k": "tao_tk_ph", "n": "Tạo TK phụ huynh 1 (mật khẩu 123456)", "t": "check"}]
        self.hop_thoai_form("Sửa hồ sơ học sinh" if sua else "Thêm hồ sơ học sinh", truong, luu, bd)

    def xoa_hoc_sinh(self) -> None:
        hs = self.hs_dang_chon()
        if hs is None:
            return
        if not self.ht.co_quyen_sua(hs):
            messagebox.showwarning("Không có quyền", "Bạn chỉ được xóa học sinh thuộc lớp mình phụ trách.", parent=self)
            return
        if not messagebox.askyesno("Xác nhận xóa", f"Xóa hồ sơ {hs.ma} - {hs.ho_ten}?\nThao tác không thể hoàn tác.",
                                   icon="warning", parent=self):
            return
        try:
            self.ht.xoa_ho_so(hs)
        except LoiNghiepVu as e:
            self.loi(e)
            return
        self.nap_ds_hs()

    def chuyen_lop_gui(self) -> None:
        hs = self.hs_dang_chon()
        if hs is None:
            return
        if not self.ht.la_quan_tri():
            messagebox.showwarning("Không có quyền", "Chỉ quản trị viên được chuyển lớp.", parent=self)
            return
        cu = hs.lop_hien_tai
        ds = [self.nhan_lop(l) for l in sorted(self.ht.lop_hoc.values(), key=lambda x: x.ma_lop) if l is not cu]

        def luu(v):
            lop = self.lop_tu_nhan(v["lop"])
            if lop is None:
                raise LoiNghiepVu("Hãy chọn lớp mới.")
            self.ht.chuyen_lop(hs, lop)

        self.hop_thoai_form(f"Chuyển lớp: {hs.ho_ten}", [
            {"k": "hien", "n": "Lớp hiện tại", "d": True, "v": cu.ten_lop if cu else CHUA_XEP_LOP},
            {"k": "lop", "n": "Chuyển sang lớp", "t": "combo", "o": ds}], luu, nut_luu="Chuyển lớp")

    # ---------------------------------------------------------------- CSV
    def xuat_csv_gui(self) -> None:
        d = self.chon_noi_luu("danh_sach_hoc_sinh.csv", ".csv", "CSV")
        if d:
            self.ht.xuat_csv(d, self.ds_dang_hien)
            self.thanh_cong(f"Đã xuất {len(self.ds_dang_hien)} học sinh:\n{d}")

    def csv_mau_gui(self) -> None:
        d = self.chon_noi_luu("mau_nhap_hoc_sinh.csv", ".csv", "CSV")
        if d:
            self.thanh_cong("Đã tạo tệp mẫu:\n" + self.ht.xuat_csv_mau(d))

    def nhap_csv_gui(self) -> None:
        if not self.ht.la_quan_tri():
            messagebox.showwarning("Không có quyền", "Chỉ quản trị viên được nhập dữ liệu hàng loạt.", parent=self)
            return
        d = filedialog.askopenfilename(parent=self, filetypes=[("CSV", "*.csv")])
        if not d:
            return
        try:
            ok, loi = self.ht.nhap_csv(d)
        except (LoiNghiepVu, OSError, UnicodeDecodeError) as e:
            self.loi(e)
            return
        msg = f"Đã nhập thành công {ok} học sinh."
        if loi:
            msg += f"\n{len(loi)} dòng bị bỏ qua:\n" + "\n".join(loi[:12]) + ("\n…" if len(loi) > 12 else "")
        messagebox.showinfo("Kết quả nhập CSV", msg, parent=self)
        self.nap_ds_hs()
