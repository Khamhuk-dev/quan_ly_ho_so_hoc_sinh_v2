# -*- coding: utf-8 -*-
"""Điểm khởi chạy:  python main.py"""
import sys

if sys.version_info < (3, 8):
    sys.exit("Cần Python 3.8 trở lên.")

try:
    import tkinter  # noqa: F401
except ImportError:
    sys.exit("Python của bạn chưa có tkinter.\n"
             "  Windows/macOS: cài lại Python từ python.org (tick 'tcl/tk').\n"
             "  Ubuntu/Debian: sudo apt install python3-tk")

from app.services import HeThong
from app.gui.app import UngDungGUI


def main() -> None:
    if sys.platform.startswith("win"):           # chữ sắc nét trên màn hình độ phân giải cao
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    ht = HeThong()
    UngDungGUI(ht).mainloop()


if __name__ == "__main__":
    main()
