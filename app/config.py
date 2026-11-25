# -*- coding: utf-8 -*-
"""Cấu hình chung + xác định nơi lưu dữ liệu (đường dẫn TUYỆT ĐỐI, không phụ thuộc thư mục chạy)."""
import os

TEN_UNG_DUNG = "Quản lý hồ sơ học sinh"
PHIEN_BAN = "2.0"
DINH_DANG_NGAY = "%d/%m/%Y"
SO_LAN_SAI_TOI_DA = 5
MAT_KHAU_MAC_DINH = "123456"      # mật khẩu khi hệ thống tự tạo tài khoản cho học sinh/phụ huynh mới
SO_BAN_SAO_LUU_TOI_DA = 15
SO_DONG_NHAT_KY_TOI_DA = 5000
TEN_TEP_DB = "hocsinh.db"

# Thư mục chứa chương trình (thư mục cha của "app")
THU_MUC_UNG_DUNG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ghi_duoc(thu_muc: str) -> bool:
    try:
        os.makedirs(thu_muc, exist_ok=True)
        thu = os.path.join(thu_muc, ".thu_ghi")
        with open(thu, "w") as f:
            f.write("ok")
        os.remove(thu)
        return True
    except OSError:
        return False


def xac_dinh_thu_muc_du_lieu() -> str:
    """Ưu tiên: biến môi trường QLHS_DATA_DIR  ->  <thư mục chương trình>/data  ->  ~/QuanLyHoSoHocSinh"""
    ung_vien = []
    if os.environ.get("QLHS_DATA_DIR"):
        ung_vien.append(os.environ["QLHS_DATA_DIR"])
    ung_vien.append(os.path.join(THU_MUC_UNG_DUNG, "data"))
    ung_vien.append(os.path.join(os.path.expanduser("~"), "QuanLyHoSoHocSinh"))
    for tm in ung_vien:
        tm = os.path.abspath(tm)
        if _ghi_duoc(tm):
            return tm
    raise RuntimeError("Không tìm được thư mục có quyền ghi để lưu dữ liệu.")


THU_MUC_DU_LIEU = xac_dinh_thu_muc_du_lieu()
DUONG_DAN_DB = os.path.join(THU_MUC_DU_LIEU, TEN_TEP_DB)
THU_MUC_SAO_LUU = os.path.join(THU_MUC_DU_LIEU, "sao_luu")
THU_MUC_XUAT = os.path.join(THU_MUC_DU_LIEU, "xuat_file")
