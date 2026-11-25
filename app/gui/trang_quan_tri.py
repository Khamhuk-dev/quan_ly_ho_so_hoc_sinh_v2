# -*- coding: utf-8 -*-
"""Các trang quản trị: lớp, môn, giáo viên, năm học, tài khoản, hệ thống."""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..enums import GioiTinh, VaiTro
from ..models import GiaoVien
from ..utils import LoiNghiepVu, chuoi_ngay, ngay_hop_le, so_nguyen
from .nen import FONT, MAU_NEN, MAU_PHU, TAT_CA, enum_tu_nhan, nhan_enum

KHONG_CO = "(Không có)"


class TrangQuanTri:
    def _khung_bang(self, p, cot, nut_def, cao=14):
        """Dựng thanh nút + bảng; nut_def: [(chữ, hàm, kiểu)]"""
        nut = tk.Frame(p, bg=MAU_NEN)
        nut.pack(fill="x", pady=(0, 8))
        for chu, ham, kieu in nut_def:
            self.nut(nut, chu, ham, kieu).pack(side="left", padx=(0, 8))
        the = self.the(p, padding=8)
        the.pack(fill="both", expand=True)
        return self.tao_bang(the, cot, cao)

    # ============================================================ LỚP HỌC
    def trang_lop_hoc(self, p) -> None:
        ht = self.ht
        self.bang_lop = self._khung_bang(p, [("ma", "Mã lớp", 80), ("ten", "Tên lớp", 90), ("khoi", "Khối", 60),
                                             ("ss", "Sĩ số", 80), ("gvcn", "GVCN", 200), ("nam", "Năm học", 100)], [
            ("＋ Thêm lớp", lambda: self.form_lop(None), "Primary"), ("Sửa", self.sua_lop_gui, ""),
            ("Phân công giảng dạy", self.phan_cong_gui, ""), ("Xóa", self.xoa_lop_gui, "Danger")])

        def nap():
            self.do_bang(self.bang_lop, [(l.ma_lop, (l.ma_lop, l.ten_lop, l.khoi, f"{l.dem_si_so()}/{l.si_so_toi_da}",
                                                    l.giao_vien_chu_nhiem.ho_ten if l.giao_vien_chu_nhiem else "-",
                                                    l.nam_hoc.ten_nam_hoc if l.nam_hoc else "-"))
                                         for l in sorted(ht.lop_hoc.values(), key=lambda x: x.ma_lop)])
        self._lam_moi = nap
        nap()

    def form_lop(self, lop) -> None:
        ht = self.ht
        gvs = [KHONG_CO] + [self.nhan_gv(g) for g in sorted(ht.giao_vien.values(), key=lambda x: x.ma) if g.ma != "GV00"]
        nam = ht.nam_hoc_hien_tai()
        bd = ({"ma": lop.ma_lop, "ten": lop.ten_lop, "khoi": str(lop.khoi), "ss": str(lop.si_so_toi_da),
               "gvcn": self.nhan_gv(lop.giao_vien_chu_nhiem) if lop.giao_vien_chu_nhiem else KHONG_CO,
               "nam": lop.nam_hoc.ten_nam_hoc if lop.nam_hoc else ""} if lop else
              {"khoi": "10", "ss": "40", "gvcn": KHONG_CO, "nam": nam.ten_nam_hoc if nam else ""})

        def luu(v):
            gv = ht.giao_vien.get(v["gvcn"].split(" - ")[0]) if v["gvcn"] != KHONG_CO else None
            ss = so_nguyen(v["ss"], "Sĩ số tối đa", 1, 100)
            if lop:
                ht.sua_lop(lop, v["ten"], ss, gv)
            else:
                ht.them_lop(v["ma"], v["ten"], so_nguyen(v["khoi"], "Khối", 1, 12), ss, v["nam"], gv)
        self.hop_thoai_form("Sửa lớp" if lop else "Thêm lớp", [
            {"k": "ma", "n": "Mã lớp", "d": bool(lop)}, {"k": "ten", "n": "Tên lớp"},
            {"k": "khoi", "n": "Khối", "d": bool(lop)}, {"k": "ss", "n": "Sĩ số tối đa"},
            {"k": "gvcn", "n": "GV chủ nhiệm", "t": "combo", "o": gvs},
            {"k": "nam", "n": "Năm học", "t": "combo", "o": list(ht.nam_hoc), "d": bool(lop)}], luu, bd)

    def sua_lop_gui(self) -> None:
        iid = self.dong_chon(self.bang_lop)
        if iid:
            self.form_lop(self.ht.lop_hoc[iid])

    def xoa_lop_gui(self) -> None:
        iid = self.dong_chon(self.bang_lop)
        if iid and messagebox.askyesno("Xác nhận", f"Xóa lớp {iid}?", parent=self):
            try:
                self.ht.xoa_lop(self.ht.lop_hoc[iid])
            except LoiNghiepVu as e:
                self.loi(e)
            self.lam_moi()

    def phan_cong_gui(self) -> None:
        iid = self.dong_chon(self.bang_lop)
        if not iid:
            return
        ht, lop = self.ht, self.ht.lop_hoc[iid]
        top = tk.Toplevel(self)
        top.title(f"Phân công giảng dạy - lớp {lop.ten_lop}")
        top.configure(bg="white")
        top.transient(self)
        kh = ttk.Frame(top, style="Card.TFrame", padding=16)
        kh.pack(fill="both", expand=True)
        b = self.tao_bang(kh, [("mon", "Môn", 140), ("gv", "Giáo viên", 220), ("tu", "Từ ngày", 100)], cao=12)
        cu = self._lam_moi

        def nap():
            self.do_bang(b, [(x.mon_hoc.ma_mon, (x.mon_hoc.ten_mon, x.giao_vien.ho_ten, chuoi_ngay(x.ngay_bat_dau)))
                             for x in lop.phan_cong if x.ngay_ket_thuc is None])
        self._lam_moi = lambda: (cu(), nap())

        def them():
            con = [m for m in ht.mon_hoc.values() if lop.giao_vien_day(m) is None]
            if not con:
                messagebox.showinfo("Đủ", "Mọi môn đã có giáo viên.", parent=top)
                return

            def luu(v):
                ht.them_phan_cong(ht.giao_vien[v["gv"].split(" - ")[0]], lop, ht.mon_hoc[v["mon"].split(" - ")[0]])
            self.hop_thoai_form("Thêm phân công", [
                {"k": "mon", "n": "Môn", "t": "combo", "o": [f"{m.ma_mon} - {m.ten_mon}" for m in con]},
                {"k": "gv", "n": "Giáo viên", "t": "combo",
                 "o": [self.nhan_gv(g) for g in sorted(ht.giao_vien.values(), key=lambda x: x.ma) if g.ma != "GV00"]}], luu)

        def ket_thuc():
            i = self.dong_chon(b)
            if i:
                try:
                    ht.ket_thuc_phan_cong(lop, ht.mon_hoc[i])
                except LoiNghiepVu as e:
                    self.loi(e, top)
                self.lam_moi()
        hn = ttk.Frame(kh, style="Card.TFrame")
        hn.pack(fill="x", pady=(10, 0))
        self.nut(hn, "＋ Thêm phân công", them, "Primary").pack(side="left", padx=(0, 8))
        self.nut(hn, "Kết thúc phân công", ket_thuc).pack(side="left")

        def dong():
            self._lam_moi = cu
            top.destroy()
        self.nut(hn, "Đóng", dong).pack(side="right")
        top.protocol("WM_DELETE_WINDOW", dong)
        nap()
        self.can_giua(top)

    # ============================================================ MÔN HỌC
    def trang_mon_hoc(self, p) -> None:
        ht = self.ht
        self.bang_mon = self._khung_bang(p, [("ma", "Mã môn", 90), ("ten", "Tên môn", 200), ("tc", "Tín chỉ", 80),
                                             ("hs", "Hệ số", 80), ("gv", "Số GV dạy", 90)], [
            ("＋ Thêm môn", lambda: self.form_mon(None), "Primary"), ("Sửa", self.sua_mon_gui, ""),
            ("Xóa", self.xoa_mon_gui, "Danger")])

        def nap():
            self.do_bang(self.bang_mon, [(m.ma_mon, (m.ma_mon, m.ten_mon, m.so_tin_chi, m.he_so,
                                                    len({x.giao_vien for x in ht.phan_cong if x.mon_hoc is m and x.ngay_ket_thuc is None})))
                                         for m in sorted(ht.mon_hoc.values(), key=lambda x: x.ma_mon)])
        self._lam_moi = nap
        nap()

    def form_mon(self, m) -> None:
        def luu(v):
            tc, hs = so_nguyen(v["tc"], "Số tín chỉ", 1, 10), so_nguyen(v["hs"], "Hệ số", 1, 3)
            self.ht.sua_mon(m, v["ten"], tc, hs) if m else self.ht.them_mon(v["ma"], v["ten"], tc, hs)
        self.hop_thoai_form("Sửa môn học" if m else "Thêm môn học", [
            {"k": "ma", "n": "Mã môn", "d": bool(m)}, {"k": "ten", "n": "Tên môn"},
            {"k": "tc", "n": "Số tín chỉ"}, {"k": "hs", "n": "Hệ số (1–3)"}], luu,
            {"ma": m.ma_mon, "ten": m.ten_mon, "tc": str(m.so_tin_chi), "hs": str(m.he_so)} if m else {"tc": "1", "hs": "1"})

    def sua_mon_gui(self) -> None:
        iid = self.dong_chon(self.bang_mon)
        if iid:
            self.form_mon(self.ht.mon_hoc[iid])

    def xoa_mon_gui(self) -> None:
        iid = self.dong_chon(self.bang_mon)
        if iid and messagebox.askyesno("Xác nhận", f"Xóa môn {iid}?", parent=self):
            try:
                self.ht.xoa_mon(self.ht.mon_hoc[iid])
            except LoiNghiepVu as e:
                self.loi(e)
            self.lam_moi()

    # ============================================================ GIÁO VIÊN
    def trang_giao_vien(self, p) -> None:
        ht = self.ht
        self.bang_gv = self._khung_bang(p, [("ma", "Mã", 60), ("ten", "Họ tên", 170), ("cm", "Chuyên môn", 90),
                                            ("td", "Trình độ", 80), ("sdt", "Điện thoại", 100), ("cn", "Chủ nhiệm", 80),
                                            ("tk", "Tài khoản", 80)], [
            ("＋ Thêm giáo viên", lambda: self.form_gv(None), "Primary"), ("Sửa", self.sua_gv_gui, ""),
            ("Xóa", self.xoa_gv_gui, "Danger")])

        def nap():
            self.do_bang(self.bang_gv, [(g.ma, (g.ma, g.ho_ten, g.chuyen_mon, g.trinh_do, g.so_dien_thoai,
                                               ", ".join(l.ten_lop for l in g.lop_chu_nhiem) or "-",
                                               g.tai_khoan.ten_dang_nhap if g.tai_khoan else "-"))
                                        for g in sorted(ht.giao_vien.values(), key=lambda x: x.ma)])
        self._lam_moi = nap
        nap()

    def form_gv(self, g) -> None:
        def luu(v):
            moi = GiaoVien(v["ma"], v["ho_ten"], ngay_hop_le(v["ngay_sinh"], "Ngày sinh"), enum_tu_nhan(GioiTinh, v["gt"]),
                           v["dia_chi"], v["sdt"], v["email"], v["cm"], v["td"])
            self.ht.sua_giao_vien(g, moi) if g else self.ht.them_giao_vien(moi)
        bd = ({"ma": g.ma, "ho_ten": g.ho_ten, "ngay_sinh": chuoi_ngay(g.ngay_sinh), "gt": g.gioi_tinh.value,
               "dia_chi": g.dia_chi, "sdt": g.so_dien_thoai, "email": g.email, "cm": g.chuyen_mon, "td": g.trinh_do}
              if g else {"ma": self.ht.ma_tiep_theo("GV", 2), "gt": "Nữ", "td": "Cử nhân"})
        self.hop_thoai_form("Sửa giáo viên" if g else "Thêm giáo viên", [
            {"k": "ma", "n": "Mã giáo viên", "d": bool(g)}, {"k": "ho_ten", "n": "Họ tên"},
            {"k": "ngay_sinh", "n": "Ngày sinh (dd/mm/yyyy)"}, {"k": "gt", "n": "Giới tính", "t": "combo", "o": nhan_enum(GioiTinh)},
            {"k": "cm", "n": "Chuyên môn"}, {"k": "td", "n": "Trình độ", "t": "combo", "o": ["Cử nhân", "Thạc sĩ", "Tiến sĩ", "Khác"]},
            {"k": "dia_chi", "n": "Địa chỉ"}, {"k": "sdt", "n": "Điện thoại"}, {"k": "email", "n": "Email"}], luu, bd)

    def sua_gv_gui(self) -> None:
        iid = self.dong_chon(self.bang_gv)
        if iid:
            self.form_gv(self.ht.giao_vien[iid])

    def xoa_gv_gui(self) -> None:
        iid = self.dong_chon(self.bang_gv)
        if iid and messagebox.askyesno("Xác nhận", f"Xóa giáo viên {iid}?", parent=self):
            try:
                self.ht.xoa_giao_vien(self.ht.giao_vien[iid])
            except LoiNghiepVu as e:
                self.loi(e)
            self.lam_moi()

    # ============================================================ NĂM HỌC
    def trang_nam_hoc(self, p) -> None:
        ht = self.ht
        self.bang_nam = self._khung_bang(p, [("nam", "Năm học", 110), ("hk", "Học kỳ", 110), ("tu", "Từ ngày", 100),
                                             ("den", "Đến ngày", 100), ("lop", "Số lớp", 70)],
                                         [("＋ Thêm năm học", self.form_nam_hoc, "Primary")])

        def nap():
            self.do_bang(self.bang_nam, [(f"{n.ten_nam_hoc}|{k.ten_hoc_ky}", (n.ten_nam_hoc, k.ten_hoc_ky, chuoi_ngay(k.ngay_bat_dau),
                                                                           chuoi_ngay(k.ngay_ket_thuc), len(n.lop_hoc)))
                                         for n in sorted(ht.nam_hoc.values(), key=lambda x: x.ngay_bat_dau) for k in n.hoc_ky])
        self._lam_moi = nap
        nap()

    def form_nam_hoc(self) -> None:
        def luu(v):
            self.ht.them_nam_hoc(v["ten"], ngay_hop_le(v["bd"], "Ngày bắt đầu"), ngay_hop_le(v["kt"], "Ngày kết thúc"),
                                 ngay_hop_le(v["chia"], "Ngày kết thúc học kỳ 1"))
        self.hop_thoai_form("Thêm năm học (2 học kỳ)", [
            {"k": "ten", "n": "Tên năm học (VD 2027-2028)"}, {"k": "bd", "n": "Ngày bắt đầu (dd/mm/yyyy)"},
            {"k": "chia", "n": "Ngày kết thúc học kỳ 1"}, {"k": "kt", "n": "Ngày kết thúc năm học"}], luu)

    # ============================================================ TÀI KHOẢN
    def trang_tai_khoan(self, p) -> None:
        ht = self.ht
        loc = tk.Frame(p, bg=MAU_NEN)
        loc.pack(fill="x", pady=(0, 6))
        self.v_tk_kw, self.v_tk_vt = tk.StringVar(), tk.StringVar(value=TAT_CA)
        ttk.Label(loc, text="Tìm tên đăng nhập / mã:").pack(side="left")
        ttk.Entry(loc, textvariable=self.v_tk_kw, width=20).pack(side="left", padx=(6, 14))
        self.thanh_chon(loc, "Vai trò:", self.v_tk_vt, [TAT_CA] + nhan_enum(VaiTro), 14)
        for v in (self.v_tk_kw, self.v_tk_vt):
            v.trace_add("write", lambda *_: self.nap_tk())
        self.bang_tk = self._khung_bang(p, [("ten", "Tên đăng nhập", 110), ("vt", "Vai trò", 100), ("chu", "Chủ sở hữu", 200),
                                            ("tt", "Trạng thái", 90), ("cuoi", "Đăng nhập cuối", 140)], [
            ("＋ Tạo tài khoản", self.form_tk, "Primary"), ("Khóa / Mở khóa", self.khoa_tk, ""),
            ("Đặt lại mật khẩu", self.dat_lai_mk, ""), ("Xóa", self.xoa_tk, "Danger")], cao=13)
        self._lam_moi = self.nap_tk
        self.nap_tk()

    def nap_tk(self) -> None:
        kw, vt = self.v_tk_kw.get().strip().lower(), self.v_tk_vt.get()
        ds = [t for t in self.ht.tai_khoan.values()
              if (not kw or kw in t.ten_dang_nhap or kw in t.chu_so_huu.ma.lower() or kw in t.chu_so_huu.ho_ten.lower())
              and (vt == TAT_CA or t.vai_tro.value == vt)]
        ds.sort(key=lambda t: (t.vai_tro.value, t.ten_dang_nhap))
        self.do_bang(self.bang_tk, [(t.ten_dang_nhap, (t.ten_dang_nhap, t.vai_tro.value, f"{t.chu_so_huu.ma} - {t.chu_so_huu.ho_ten}",
                                                      "Hoạt động" if t.hoat_dong else "Đã khóa", t.lan_dang_nhap_cuoi or "-"))
                                    for t in ds[:400]], {t.ten_dang_nhap: "canh_bao" for t in ds if not t.hoat_dong})

    def form_tk(self) -> None:
        ht = self.ht

        def luu(v):
            nguoi = ht.nguoi_theo_ma(v["ma"])
            if nguoi is None:
                raise LoiNghiepVu("Không tìm thấy người có mã này.")
            vt = (enum_tu_nhan(VaiTro, v["vt"]) if isinstance(nguoi, GiaoVien) else
                  VaiTro.HOC_SINH if nguoi.vai_tro_mac_dinh is VaiTro.HOC_SINH else VaiTro.PHU_HUYNH)
            ht.tao_tai_khoan(nguoi, v["ten"] or nguoi.ma.lower(), v["mk"], vt)
        self.hop_thoai_form("Tạo tài khoản", [
            {"k": "ma", "n": "Mã người dùng (HS/GV/PH)"}, {"k": "ten", "n": "Tên đăng nhập (để trống = mã)"},
            {"k": "mk", "n": "Mật khẩu (≥ 6 ký tự)", "t": "pw"},
            {"k": "vt", "n": "Vai trò (chỉ áp dụng cho giáo viên)", "t": "combo", "o": [VaiTro.GIAO_VIEN.value, VaiTro.QUAN_TRI.value]}],
            luu, {"vt": VaiTro.GIAO_VIEN.value})

    def _tk_chon(self):
        iid = self.dong_chon(self.bang_tk)
        return self.ht.tai_khoan.get(iid) if iid else None

    def khoa_tk(self) -> None:
        t = self._tk_chon()
        if t:
            try:
                self.ht.khoa_mo_tai_khoan(t)
            except LoiNghiepVu as e:
                self.loi(e)
            self.lam_moi()

    def dat_lai_mk(self) -> None:
        t = self._tk_chon()
        if t:
            self.hop_thoai_form(f"Đặt lại mật khẩu: {t.ten_dang_nhap}",
                                [{"k": "mk", "n": "Mật khẩu mới (≥ 6 ký tự)", "t": "pw"}],
                                lambda v: self.ht.dat_lai_mat_khau(t, v["mk"]))

    def xoa_tk(self) -> None:
        t = self._tk_chon()
        if t and messagebox.askyesno("Xác nhận", f"Xóa tài khoản {t.ten_dang_nhap}?", parent=self):
            try:
                self.ht.xoa_tai_khoan(t)
            except LoiNghiepVu as e:
                self.loi(e)
            self.lam_moi()

    # ============================================================ HỆ THỐNG
    def trang_he_thong(self, p) -> None:
        nb = ttk.Notebook(p)
        nb.pack(fill="both", expand=True)
        t1 = ttk.Frame(nb, style="Card.TFrame", padding=18)
        t2 = ttk.Frame(nb, style="Card.TFrame", padding=12)
        t3 = ttk.Frame(nb, style="Card.TFrame", padding=12)
        nb.add(t1, text="Thông tin & dữ liệu")
        nb.add(t2, text="Sao lưu / khôi phục")
        nb.add(t3, text="Nhật ký hoạt động")
        self.kv_info = ttk.Frame(t1, style="Card.TFrame")
        self.kv_info.pack(fill="x")
        hn = ttk.Frame(t1, style="Card.TFrame")
        hn.pack(fill="x", pady=(16, 0))
        self.nut(hn, "💾 Lưu ngay", self.luu_ngay, "Primary").pack(side="left", padx=(0, 8))
        self.nut(hn, "Mở thư mục dữ liệu", lambda: self.mo_tep(os.path.dirname(self.ht.duong_dan_db))).pack(side="left", padx=(0, 8))
        self.nut(hn, "Nhập dữ liệu từ hocsinh.txt (bản cũ)…", self.nhap_cu_gui).pack(side="left")
        ttk.Label(t1, style="Muted.TLabel", wraplength=700, justify="left", text=(
            "\nDữ liệu được ghi vào tệp cơ sở dữ liệu SQLite ngay sau mỗi thao tác và khi đóng chương trình, nên tắt/mở lại "
            "vẫn còn nguyên. Để chuyển dữ liệu sang máy khác, hãy sao chép cả thư mục 'data'.")).pack(anchor="w")
        bar = ttk.Frame(t2, style="Card.TFrame")
        bar.pack(fill="x", pady=(0, 8))
        self.nut(bar, "Sao lưu ngay", self.sao_luu_gui, "Primary").pack(side="left", padx=(0, 8))
        self.nut(bar, "Khôi phục bản đã chọn", self.phuc_hoi_gui).pack(side="left", padx=(0, 8))
        self.nut(bar, "Khôi phục từ tệp…", lambda: self.phuc_hoi_gui(True)).pack(side="left")
        self.bang_sl = self.tao_bang(t2, [("ten", "Tệp sao lưu", 360), ("tg", "Thời điểm", 150), ("kt", "Dung lượng", 90, "e")], cao=12)
        loc = ttk.Frame(t3, style="Card.TFrame")
        loc.pack(fill="x", pady=(0, 8))
        self.v_nk = tk.StringVar()
        ttk.Label(loc, text="Tìm trong nhật ký:", style="Card.TLabel").pack(side="left")
        ttk.Entry(loc, textvariable=self.v_nk, width=30).pack(side="left", padx=8)
        self.v_nk.trace_add("write", lambda *_: self.nap_nhat_ky())
        self.bang_nk = self.tao_bang(t3, [("tg", "Thời gian", 140), ("nguoi", "Người dùng", 90), ("hd", "Hành động", 190),
                                          ("ct", "Chi tiết", 330)], cao=14)
        self._lam_moi = self.nap_he_thong
        self.nap_he_thong()

    def nap_he_thong(self) -> None:
        for w in self.kv_info.winfo_children():
            w.destroy()
        t = self.ht.thong_tin_he_thong()
        dong = [("Tệp dữ liệu", t["tep_du_lieu"]), ("Dung lượng", f"{t['dung_luong'] / 1024:.0f} KB"),
                ("Thư mục sao lưu", f"{t['thu_muc_sao_luu']}  ({t['so_ban_sao_luu']} bản)"),
                ("Học sinh / Phụ huynh", f"{t['so_hs']} / {t['so_ph']}"), ("Giáo viên / Lớp / Môn", f"{t['so_gv']} / {t['so_lop']} / {t['so_mon']}"),
                ("Tài khoản", str(t["so_tai_khoan"])), ("Số bản ghi điểm / điểm danh", f"{t['so_diem']} / {t['so_diem_danh']}"),
                ("Lưu lần cuối", t["lan_luu_cuoi"].strftime("%H:%M:%S %d/%m/%Y") if t["lan_luu_cuoi"] else "-")]
        for i, (k, v) in enumerate(dong):
            ttk.Label(self.kv_info, text=k, style="Muted.TLabel").grid(row=i, column=0, sticky="w", pady=3, padx=(0, 24))
            ttk.Label(self.kv_info, text=v, style="Card.TLabel").grid(row=i, column=1, sticky="w", pady=3)
        ds = self.ht.danh_sach_sao_luu()
        self.do_bang(self.bang_sl, [(f, (os.path.basename(f), self._tg_tep(f), f"{os.path.getsize(f) / 1024:.0f} KB")) for f in ds])
        self.nap_nhat_ky()

    @staticmethod
    def _tg_tep(f: str) -> str:
        from datetime import datetime
        return datetime.fromtimestamp(os.path.getmtime(f)).strftime("%d/%m/%Y %H:%M:%S")

    def nap_nhat_ky(self) -> None:
        rows = self.ht.kho.doc_nhat_ky(500, self.v_nk.get().strip())
        self.do_bang(self.bang_nk, [(str(i), r) for i, r in enumerate(rows)])

    def luu_ngay(self) -> None:
        self.ht.luu_du_lieu()
        self.nap_he_thong()
        self.thanh_cong("Đã lưu toàn bộ dữ liệu.")

    def sao_luu_gui(self) -> None:
        self.thanh_cong("Đã sao lưu:\n" + self.ht.sao_luu_ngay())
        self.nap_he_thong()

    def phuc_hoi_gui(self, tu_tep: bool = False) -> None:
        if tu_tep is True:
            f = filedialog.askopenfilename(parent=self, filetypes=[("Sao lưu", "*.db")], initialdir=self.ht.thu_muc_sao_luu)
        else:
            f = self.dong_chon(self.bang_sl)
        if not f:
            return
        if not messagebox.askyesno("Khôi phục dữ liệu", "Dữ liệu hiện tại sẽ được sao lưu rồi thay bằng bản này.\n"
                                   "Bạn sẽ phải đăng nhập lại. Tiếp tục?", icon="warning", parent=self):
            return
        try:
            self.ht.phuc_hoi(f)
        except LoiNghiepVu as e:
            self.loi(e)
            return
        messagebox.showinfo("Hoàn tất", "Đã khôi phục dữ liệu. Vui lòng đăng nhập lại.", parent=self)
        self.hien_dang_nhap()

    def nhap_cu_gui(self) -> None:
        f = filedialog.askopenfilename(parent=self, title="Chọn tệp hocsinh.txt của phiên bản cũ",
                                       filetypes=[("Dữ liệu cũ", "*.txt *.json"), ("Tất cả", "*.*")])
        if f:
            try:
                self.thanh_cong(self.ht.nhap_du_lieu_cu(f))
            except LoiNghiepVu as e:
                self.loi(e)
            self.nap_he_thong()
