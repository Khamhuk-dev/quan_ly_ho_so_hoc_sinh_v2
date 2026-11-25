# -*- coding: utf-8 -*-
"""Tiện ích dùng chung: ngày tháng, bỏ dấu, mật khẩu, kiểm tra dữ liệu nhập."""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import unicodedata
from datetime import date, datetime
from typing import Optional

from .config import DINH_DANG_NGAY

SO_LAN_BAM_MAC_DINH = 150_000


class LoiNghiepVu(Exception):
    """Lỗi vi phạm quy tắc nghiệp vụ (mã trùng, điểm sai khoảng, hết chỗ...)."""


# ---------------- ngày tháng ----------------
def chuoi_ngay(d: Optional[date]) -> str:
    return d.strftime(DINH_DANG_NGAY) if d else ""


def doc_ngay(s: str) -> date:
    return datetime.strptime(s.strip(), DINH_DANG_NGAY).date()


def ngay_hop_le(s: str, ten: str, bat_buoc: bool = True) -> Optional[date]:
    s = (s or "").strip()
    if not s:
        if bat_buoc:
            raise LoiNghiepVu(f"Vui lòng nhập {ten}.")
        return None
    try:
        return doc_ngay(s)
    except ValueError:
        raise LoiNghiepVu(f"{ten} không hợp lệ (định dạng dd/mm/yyyy).")


def iso(d: Optional[date]) -> str:
    return d.isoformat() if d else ""


def tu_iso(s: Optional[str]) -> Optional[date]:
    return date.fromisoformat(s) if s else None


def so_nguyen(s: str, ten: str, thap: int, cao: int) -> int:
    try:
        v = int(str(s).strip())
    except ValueError:
        raise LoiNghiepVu(f"{ten} phải là số nguyên.")
    if not thap <= v <= cao:
        raise LoiNghiepVu(f"{ten} phải trong khoảng {thap}–{cao}.")
    return v


def so_thuc_diem(s: str) -> Optional[float]:
    """Đọc điểm 0–10 từ ô nhập (chấp nhận dấu phẩy). Ô trống -> None."""
    s = (s or "").strip().replace(",", ".")
    if not s:
        return None
    try:
        v = float(s)
    except ValueError:
        raise LoiNghiepVu(f"'{s}' không phải là số.")
    if not 0 <= v <= 10:
        raise LoiNghiepVu(f"Điểm '{s}' nằm ngoài khoảng 0–10.")
    return round(v, 2)


# ---------------- chuỗi ----------------
def bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def kiem_tra_sdt(s: str) -> bool:
    return bool(re.fullmatch(r"\+?\d{8,15}", s))


def kiem_tra_email(s: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s))


# ---------------- mật khẩu ----------------
def ma_hoa_mat_khau(mat_khau: str, salt: Optional[str] = None, so_lan: int = SO_LAN_BAM_MAC_DINH) -> str:
    """Định dạng lưu: pbkdf2$<số lần>$<salt>$<hash>"""
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", mat_khau.encode("utf-8"), bytes.fromhex(salt), so_lan)
    return f"pbkdf2${so_lan}${salt}${h.hex()}"


def kiem_tra_mat_khau(mat_khau: str, da_luu: str) -> bool:
    p = da_luu.split("$")
    try:
        if p[0] == "pbkdf2":                       # định dạng mới
            so_lan, salt = int(p[1]), p[2]
        else:                                       # định dạng cũ của phiên bản 1: salt$hash (200.000 lần)
            so_lan, salt = 200_000, p[0]
        return hmac.compare_digest(ma_hoa_mat_khau(mat_khau, salt, so_lan), da_luu if p[0] == "pbkdf2"
                                   else f"pbkdf2${so_lan}${salt}${p[1]}")
    except (ValueError, IndexError):
        return False


# ---------------- học lực ----------------
def xep_loai_hoc_luc(dtb: float) -> str:
    if dtb >= 8.0:
        return "Giỏi"
    if dtb >= 6.5:
        return "Khá"
    if dtb >= 5.0:
        return "Trung bình"
    return "Yếu"


def dinh_dang_dtb(v: Optional[float]) -> str:
    return f"{v:.2f}" if v else "-"
