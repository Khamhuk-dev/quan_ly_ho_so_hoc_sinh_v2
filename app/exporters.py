# -*- coding: utf-8 -*-
"""Xuất tệp: PDF (không cần thư viện ngoài), HTML in được (có đủ dấu tiếng Việt), CSV."""
from __future__ import annotations

import csv
import html
import textwrap
from typing import List, Optional

from .utils import bo_dau, chuoi_ngay, xep_loai_hoc_luc


def xuat_pdf_ho_so(ho_so, duong_dan: Optional[str] = None) -> str:
    """Xuất hồ sơ ra file PDF 1 trang (bỏ dấu tiếng Việt vì PDF cơ bản không nhúng font)."""
    hs = ho_so.hoc_sinh
    duong_dan = duong_dan or f"hoso_{hs.ma_hoc_sinh}.pdf"
    lop = hs.lop_hien_tai
    dong = ["HO SO HOC SINH", "",
            f"Ma ho so      : {ho_so.ma_ho_so}", f"Ma hoc sinh   : {hs.ma_hoc_sinh}",
            f"Ho ten        : {hs.ho_ten}", f"Ngay sinh     : {chuoi_ngay(hs.ngay_sinh)}",
            f"Gioi tinh     : {hs.gioi_tinh.value}", f"Noi sinh      : {hs.noi_sinh}",
            f"Dan toc       : {hs.dan_toc}", f"CMND/CCCD     : {hs.so_cccd}",
            f"Dia chi       : {hs.dia_chi}",
            f"So dien thoai : {hs.so_dien_thoai}", f"Email         : {hs.email}",
            f"Lop           : {lop.ten_lop if lop else '(chua xep lop)'}",
            f"Trang thai    : {hs.trang_thai.value}", f"Ngay nhap hoc : {chuoi_ngay(hs.ngay_nhap_hoc)}",
            f"Suc khoe      : {ho_so.ghi_chu_suc_khoe}", f"Thanh tich    : {ho_so.thanh_tich}",
            f"Ky luat       : {ho_so.ghi_chu_ky_luat}", f"Ngay tao ho so: {chuoi_ngay(ho_so.ngay_tao)}"]
    dong += [f"Phu huynh     : {p.ho_ten} ({p.quan_he}) - {p.so_dien_thoai}" for p in hs.phu_huynh]
    dong = [ln for d in dong for ln in (textwrap.wrap(bo_dau(d), 90) or [""])][:48]

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    nd = "BT /F1 12 Tf 50 800 Td 16 TL\n" + "\n".join(f"({esc(d)}) Tj T*" for d in dong) + "\nET"
    nd = nd.encode("latin-1", "replace").decode("latin-1")
    objs = ["<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
            "/Resources << /Font << /F1 5 0 R >> >> >>",
            f"<< /Length {len(nd)} >>\nstream\n{nd}\nendstream",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"]
    out, vt = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        vt.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xr = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{v:010d} 00000 n \n" for v in vt).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xr}\n%%EOF\n".encode()
    with open(duong_dan, "wb") as f:
        f.write(out)
    return duong_dan


def _e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def xuat_html_ho_so(hs, duong_dan: str, hoc_ky=None) -> str:
    """Phiếu hồ sơ + bảng điểm in được (mở bằng trình duyệt, Ctrl+P để in hoặc lưu PDF có dấu)."""
    r, lop = hs.ho_so, hs.lop_hien_tai
    hang_tt = [("Mã học sinh", hs.ma_hoc_sinh), ("Họ và tên", hs.ho_ten), ("Ngày sinh", chuoi_ngay(hs.ngay_sinh)),
               ("Giới tính", hs.gioi_tinh.value), ("Nơi sinh", hs.noi_sinh), ("Dân tộc", hs.dan_toc),
               ("CMND/CCCD", hs.so_cccd), ("Địa chỉ", hs.dia_chi), ("Điện thoại", hs.so_dien_thoai),
               ("Email", hs.email), ("Lớp", lop.ten_lop if lop else "(chưa xếp lớp)"),
               ("GVCN", lop.giao_vien_chu_nhiem.ho_ten if lop and lop.giao_vien_chu_nhiem else ""),
               ("Trạng thái", hs.trang_thai.value), ("Ngày nhập học", chuoi_ngay(hs.ngay_nhap_hoc)),
               ("Sức khỏe", r.ghi_chu_suc_khoe), ("Thành tích", r.thanh_tich), ("Kỷ luật", r.ghi_chu_ky_luat)]
    for p in hs.phu_huynh:
        hang_tt.append((f"Phụ huynh ({p.quan_he})", f"{p.ho_ten} · {p.so_dien_thoai} · {p.nghe_nghiep}"))
    body = ["<h1>HỒ SƠ HỌC SINH</h1>", "<table class='tt'>"]
    body += [f"<tr><th>{_e(k)}</th><td>{_e(v) or '—'}</td></tr>" for k, v in hang_tt]
    body.append("</table>")
    if hoc_ky is not None:
        body.append(f"<h2>Kết quả học tập — {_e(hoc_ky)}</h2>")
        body.append("<table class='d'><tr><th>Môn</th><th>Thường xuyên</th><th>Giữa kỳ</th><th>Cuối kỳ</th><th>TB môn</th></tr>")
        for m in sorted({d.mon_hoc for d in hs.diem if d.hoc_ky is hoc_ky}, key=lambda m: m.ma_mon):
            ds = [d for d in hs.diem if d.mon_hoc is m and d.hoc_ky is hoc_ky]
            lay = lambda ten: ", ".join(f"{d.gia_tri:g}" for d in ds if d.loai_diem.name == ten) or "-"
            body.append(f"<tr><td>{_e(m.ten_mon)}</td><td>{lay('THUONG_XUYEN')}</td><td>{lay('GIUA_KY')}</td>"
                        f"<td>{lay('CUOI_KY')}</td><td><b>{hs.diem_mon(m, hoc_ky):.2f}</b></td></tr>")
        body.append("</table>")
        dtb = hs.tinh_diem_trung_binh(hoc_ky)
        hk = hs.hanh_kiem_hoc_ky(hoc_ky)
        body.append(f"<p><b>Điểm trung bình:</b> {dtb:.2f} &nbsp; <b>Học lực:</b> "
                    f"{xep_loai_hoc_luc(dtb) if dtb else '-'} &nbsp; <b>Hạnh kiểm:</b> "
                    f"{_e(hk.xep_loai.value) if hk else 'chưa xếp loại'}</p>")
    noi_dung = ("<!doctype html><html lang='vi'><head><meta charset='utf-8'><title>Hồ sơ " + _e(hs.ho_ten) + "</title>"
                "<style>body{font-family:'Segoe UI',Arial,sans-serif;max-width:800px;margin:30px auto;color:#0f172a}"
                "h1{text-align:center;color:#1d4ed8}h2{color:#1d4ed8;margin-top:28px}"
                "table{border-collapse:collapse;width:100%}th,td{border:1px solid #cbd5e1;padding:6px 10px;text-align:left}"
                ".tt th{width:30%;background:#f1f5f9}.d th{background:#e2e8f0}@media print{body{margin:0}}</style></head><body>"
                + "\n".join(body) + "</body></html>")
    with open(duong_dan, "w", encoding="utf-8") as f:
        f.write(noi_dung)
    return duong_dan


def ghi_csv(duong_dan: str, tieu_de: List[str], hang: List[list]) -> str:
    with open(duong_dan, "w", newline="", encoding="utf-8-sig") as f:      # utf-8-sig: Excel đọc đúng tiếng Việt
        w = csv.writer(f)
        w.writerow(tieu_de)
        w.writerows(hang)
    return duong_dan
