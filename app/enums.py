# -*- coding: utf-8 -*-
from enum import Enum


class XepLoaiHanhKiem(Enum):
    TOT = "Tốt"
    KHA = "Khá"
    TRUNG_BINH = "Trung bình"
    YEU = "Yếu"


class LoaiDiem(Enum):
    THUONG_XUYEN = "Thường xuyên"
    GIUA_KY = "Giữa kỳ"
    CUOI_KY = "Cuối kỳ"


class VaiTro(Enum):
    QUAN_TRI = "Quản trị viên"
    GIAO_VIEN = "Giáo viên"
    HOC_SINH = "Học sinh"
    PHU_HUYNH = "Phụ huynh"


class TrangThaiDiemDanh(Enum):
    CO_MAT = "Có mặt"
    VANG_CO_PHEP = "Vắng có phép"
    VANG_KHONG_PHEP = "Vắng không phép"
    DI_MUON = "Đi muộn"


class GioiTinh(Enum):
    NAM = "Nam"
    NU = "Nữ"
    KHAC = "Khác"


class TrangThaiHocSinh(Enum):
    DANG_HOC = "Đang học"
    BAO_LUU = "Bảo lưu"
    CHUYEN_TRUONG = "Chuyển trường"
    DA_TOT_NGHIEP = "Đã tốt nghiệp"
