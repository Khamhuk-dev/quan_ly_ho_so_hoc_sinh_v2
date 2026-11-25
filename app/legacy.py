# -*- coding: utf-8 -*-
"""Nhập dữ liệu từ tệp JSON cũ (hocsinh.txt của phiên bản 1) vào hệ thống hiện tại.

Chỉ GỘP thêm: học sinh/phụ huynh có mã chưa tồn tại mới được thêm; dữ liệu đang có không bị ghi đè.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Optional

from .enums import (GioiTinh, LoaiDiem, TrangThaiDiemDanh, TrangThaiHocSinh, XepLoaiHanhKiem)
from .models import Diem, DiemDanh, GhiDanh, HocSinh, HoSoHocSinh, KetQuaHanhKiem, PhuHuynh
from .utils import LoiNghiepVu, doc_ngay


def nhap_json_cu(ht, duong_dan: str) -> str:
    try:
        with open(duong_dan, encoding="utf-8") as f:
            d = json.load(f)
        ds_hs, ds_ph = d["hoc_sinh"], d.get("phu_huynh", [])
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise LoiNghiepVu(f"Không đọc được tệp dữ liệu cũ: {e}")

    ng = lambda s: doc_ngay(s) if s else None
    hk_khoa = {k.khoa: k for k in ht.hoc_ky_tat_ca()}
    ph_cu = {p["ma"]: p for p in ds_ph}
    them_hs = them_ph = bo_qua = 0
    for x in ds_hs:
        ma = x["ma"].strip().upper()
        if ht.kiem_tra_ma_trung(ma):
            bo_qua += 1
            continue
        try:
            h = HocSinh(ma, x["ho_ten"], ng(x["ngay_sinh"]), GioiTinh[x["gioi_tinh"]], x.get("dia_chi", ""),
                        x.get("so_dien_thoai", ""), x.get("email", ""), ng(x.get("ngay_nhap_hoc")),
                        TrangThaiHocSinh[x.get("trang_thai", "DANG_HOC")])
            r = x.get("ho_so", {})
            h.ho_so = HoSoHocSinh(h, r.get("ma_ho_so", "HS-" + ma), r.get("suc_khoe", ""), r.get("thanh_tich", ""),
                                  r.get("ky_luat", ""), ng(r.get("ngay_tao")))
        except (ValueError, KeyError, LoiNghiepVu):
            bo_qua += 1
            continue
        ht.hoc_sinh[ma] = h
        them_hs += 1
        for ma_ph in x.get("phu_huynh", []):
            ph = ht.phu_huynh.get(ma_ph)
            if ph is None and ma_ph in ph_cu and not ht.kiem_tra_ma_trung(ma_ph):
                p = ph_cu[ma_ph]
                try:
                    ph = PhuHuynh(p["ma"], p["ho_ten"], ng(p.get("ngay_sinh")), GioiTinh[p.get("gioi_tinh", "KHAC")],
                                  p.get("dia_chi", ""), p.get("so_dien_thoai", ""), p.get("email", ""),
                                  p.get("quan_he", ""), p.get("nghe_nghiep", ""))
                    ht.phu_huynh[ph.ma] = ph
                    them_ph += 1
                except (ValueError, KeyError, LoiNghiepVu):
                    ph = None
            if ph is not None:
                h.them_phu_huynh(ph)
        for g in x.get("ghi_danh", []):
            lop = ht.lop_hoc.get(g["lop"])
            if lop:
                gd = GhiDanh(h, lop, ng(g["vao"]) or date.today(), ng(g.get("ra")))
                h.ghi_danh.append(gd)
                lop.ghi_danh.append(gd)
        for e in x.get("diem", []):
            if e["mon"] in ht.mon_hoc and e["hoc_ky"] in hk_khoa:
                h.diem.append(Diem(h, ht.mon_hoc[e["mon"]], hk_khoa[e["hoc_ky"]], LoaiDiem[e["loai"]],
                                   e["gia_tri"], ng(e.get("ngay"))))
        for e in x.get("diem_danh", []):
            if e["lop"] in ht.lop_hoc:
                h.diem_danh.append(DiemDanh(h, ht.lop_hoc[e["lop"]], ng(e["ngay"]),
                                            TrangThaiDiemDanh[e["trang_thai"]], e.get("ghi_chu", "")))
        for e in x.get("hanh_kiem", []):
            if e["hoc_ky"] in hk_khoa:
                h.ket_qua_hanh_kiem.append(KetQuaHanhKiem(h, hk_khoa[e["hoc_ky"]], XepLoaiHanhKiem[e["xep_loai"]],
                                                          e.get("nhan_xet", "")))
    ht.luu_du_lieu(["nguoi", "diem", "diem_danh", "hanh_kiem"])
    return f"Đã thêm {them_hs} học sinh, {them_ph} phụ huynh; bỏ qua {bo_qua} hồ sơ trùng mã hoặc lỗi."
