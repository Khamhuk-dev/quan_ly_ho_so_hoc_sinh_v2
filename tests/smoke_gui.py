# -*- coding: utf-8 -*-
"""Kiểm tra nhanh MÃ giao diện khi máy không có màn hình/tkinter: giả lập tkinter rồi mở mọi trang với mọi vai trò.
Chạy:  python tests/smoke_gui.py   (chỉ bắt lỗi Python như sai tên hàm/biến, không kiểm tra hình thức hiển thị)"""
import os
import sys
import tempfile
import types
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Var:
    def __init__(s, master=None, value=""):
        s.v = value
    def get(s): return s.v
    def set(s, v): s.v = v
    def trace_add(s, *a): pass


class W:
    def __init__(s, *a, **k): s.k = k
    def __getattr__(s, n): return MagicMock()
    def winfo_width(s): return 600
    def winfo_height(s): return 200
    def winfo_rootx(s): return 0
    def winfo_rooty(s): return 0
    def winfo_children(s): return []
    def __getitem__(s, k): return s.k.get(k)
    def __setitem__(s, k, v): pass


NUT = []


class Button(W):
    def __init__(s, *a, **k):
        super().__init__(*a, **k)
        if "command" in k:
            NUT.append(k)


class Text(W):
    def get(s, *a): return ""


m = types.ModuleType("tkinter")
class Tk(W):
    """Tk giả nghiêm ngặt: gọi nhầm phương thức không tồn tại sẽ báo lỗi (như tkinter thật)."""
    OK = ("title", "geometry", "minsize", "configure", "bind_all", "protocol", "after", "destroy", "update_idletasks",
          "mainloop", "wait_visibility", "grab_set", "transient", "resizable", "bind", "winfo_children", "winfo_containing")
    def __getattr__(s, n):
        if n in s.OK or n.startswith("winfo_"):
            return MagicMock()
        raise AttributeError(n)


setattr(m, "Tk", Tk)
for n in ("Toplevel", "Frame", "Label", "Canvas", "Menu"):
    setattr(m, n, type(n, (W,), {}))
m.Button, m.Text = Button, Text
m.StringVar = m.BooleanVar = Var
m.TclError = Exception
sys.modules["tkinter"] = m
for n in ("filedialog", "messagebox", "ttk"):
    sub = MagicMock()
    setattr(m, n, sub)
    sys.modules["tkinter." + n] = sub
m.ttk.Treeview = type("Treeview", (W,), {})

from app.gui.app import UngDungGUI          # noqa: E402
from app.services import HeThong           # noqa: E402

ht = HeThong(os.path.join(tempfile.mkdtemp(), "x.db"))
app = UngDungGUI(ht)
loi = 0
for user, pw in [("admin", "admin123"), ("gv01", "gv123"), ("gv03", "gv123"), ("hs001", "hs123"), ("ph001", "ph123")]:
    if ht.tai_khoan_hien_tai:
        ht.dang_xuat()
    app.v_ten.set(user)
    app.v_mk.set(pw)
    app.xu_ly_dang_nhap()
    assert ht.tai_khoan_hien_tai, user
    muc = [k for k in NUT if "command" in k and k.get("text", "")[:1] != "" and "  " in k.get("text", "")]
    NUT.clear()
    app.hien_chinh()
    muc = [k for k in NUT if "  " in k.get("text", "")]
    for k in muc:
        try:
            k["command"]()
            print(f"  ok  {user:6} {k['text']}")
        except Exception as e:                       # noqa: BLE001
            import traceback
            traceback.print_exc()
            loi += 1
    # thao tác phụ trên các trang quản trị / hồ sơ
    if user in ("admin", "gv01"):
        for ten in ("trang_hoc_sinh", "trang_diem", "trang_diem_danh", "trang_thong_ke"):
            getattr(app, ten)(m.Frame())
        app.nap_ds_hs(); app.nap_bang_diem(); app.nap_hanh_kiem(); app.nap_diem_danh(); app.xem_bao_cao()
        for f in (lambda: app.form_hoc_sinh(None), lambda: app.form_hoc_sinh(ht.hoc_sinh["HS001"])):
            f()
    if user == "admin":
        for ten in ("trang_lop_hoc", "trang_mon_hoc", "trang_giao_vien", "trang_nam_hoc", "trang_tai_khoan", "trang_he_thong"):
            getattr(app, ten)(m.Frame())
        app.form_lop(None); app.form_mon(None); app.form_gv(None); app.form_nam_hoc(); app.form_tk()
        app.hop_thoai_doi_mat_khau()
print("HOÀN TẤT, số lỗi:", loi)
sys.exit(1 if loi else 0)
