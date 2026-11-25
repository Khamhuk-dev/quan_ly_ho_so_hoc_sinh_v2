# Quản lý hồ sơ học sinh – phiên bản 2.0

ภาษาไทย (สรุป): แตกไฟล์ zip แล้วดับเบิลคลิก `chay.bat` (Windows) หรือรัน `python main.py`
ข้อมูลทั้งหมดบันทึกลงไฟล์ `data/hocsinh.db` **ทันทีที่แก้ไขทุกครั้ง** และตอนปิดโปรแกรม
(ใช้ path แบบสัมบูรณ์ ไม่ขึ้นกับโฟลเดอร์ที่เปิดโปรแกรม) ปิด-เปิดใหม่ข้อมูลยังอยู่ครบ

## Chạy chương trình
Cần Python 3.8+ (có sẵn tkinter, không cần cài thư viện nào khác).

- Windows: nhấp đúp `chay.bat`  (hoặc `python main.py`)
- Linux/macOS: `./chay.sh`  (Ubuntu cần `sudo apt install python3-tk`)

Tài khoản mẫu (đổi mật khẩu sau khi đăng nhập): `admin/admin123`, `gv01/gv123`, `hs001/hs123`, `ph001/ph123`
(các giáo viên `gv02…gv24`, học sinh `hs002…`, phụ huynh `ph003…` cùng mật khẩu mẫu theo vai trò).

## Dữ liệu được lưu ở đâu?
`data/hocsinh.db` (SQLite) nằm cạnh chương trình – thanh dưới cùng của cửa sổ luôn hiện đường dẫn thật.
* Ghi ngay sau **mỗi** thao tác (transaction – mất điện giữa chừng cũng không hỏng) và khi đóng cửa sổ.
* Tự sao lưu mỗi lần mở chương trình (tối đa 15 bản trong `data/sao_luu/`); tệp hỏng sẽ tự khôi phục từ bản sao lưu gần nhất.
* Muốn chuyển sang máy khác: chép cả thư mục `data`. Muốn về dữ liệu mẫu: xóa `data/hocsinh.db`.
* Thư mục lưu có thể đổi bằng biến môi trường `QLHS_DATA_DIR`.
* Dữ liệu cũ (`hocsinh.txt` của bản 1): vào **Hệ thống, sao lưu → Nhập dữ liệu từ hocsinh.txt**.

## Chức năng
| Vai trò | Chức năng |
|---|---|
| Quản trị | Tổng quan (biểu đồ), hồ sơ học sinh (thêm/sửa/xóa/chuyển lớp, nhập–xuất CSV, in hồ sơ, PDF), nhập điểm & hạnh kiểm, điểm danh, báo cáo, quản lý lớp/phân công/môn/giáo viên/năm học/tài khoản, sao lưu–khôi phục, nhật ký hoạt động |
| Giáo viên | Như trên nhưng chỉ với lớp mình chủ nhiệm / được phân công; chỉ GVCN được xếp hạnh kiểm |
| Học sinh / Phụ huynh | Xem thông tin, điểm – học lực, điểm danh (phụ huynh chọn từng con) |

Dữ liệu mẫu: 9 lớp (10A1–12A3), ~325 học sinh (có bảo lưu / chuyển trường / tốt nghiệp / chuyển lớp), 24 giáo viên, 12 môn,
phân công giảng dạy, ~15.000 điểm, ~9.500 lượt điểm danh, hạnh kiểm, ~600 phụ huynh, ~675 tài khoản.

## Cấu trúc mã nguồn
```
main.py            điểm khởi chạy
app/config.py      cấu hình + đường dẫn dữ liệu tuyệt đối
app/models.py      các lớp miền theo biểu đồ lớp (HocSinh, LopHoc, Diem...)
app/storage.py     lưu SQLite, sao lưu, nhật ký
app/services.py    HeThong: nghiệp vụ & phân quyền
app/reports.py     báo cáo/thống kê      app/exporters.py  PDF, HTML, CSV
app/seed.py        dữ liệu mẫu           app/legacy.py     nhập dữ liệu bản cũ
app/gui/           giao diện tkinter, mỗi trang một tệp
tests/             kiểm thử:  python -m unittest discover -s tests
```
