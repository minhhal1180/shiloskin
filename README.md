# ShiloSkin

Ứng dụng đơn giản để tra cứu skin CS2, xem float/độ hiếm, quản lý kho đồ và thử mua/đổi skin bằng **xu mô phỏng SC**. Không kết nối Steam, không nhận tiền và không chuyển vật phẩm trong game thật.

**Website:** https://sv21.bcse-vju.com

Hồ sơ học phần: **Nguyễn Từ Lân – 23110306**. Bạn cặp phụ trách báo cáo kiểm thử: **Bùi Xuân Minh – 23110193**. Người dùng yêu cầu Codex hỗ trợ xây dựng cả hai ứng dụng và cả hai bộ báo cáo; không coi đây là thử nghiệm mù độc lập.

Repo `lanzymez30/shiloskin` được cung cấp ban đầu đang trống và tài khoản kết nối chỉ có quyền đọc. Mã triển khai được lưu ở bản công khai `minhhal1180/shiloskin`; có thể chuyển sang repo gốc khi chủ repo cấp quyền.

## Chạy cục bộ

Cần Python 3.11 trở lên:

```powershell
git clone https://github.com/minhhal1180/shiloskin.git
cd shiloskin
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Mở http://127.0.0.1:5000. Lần đầu tự tạo SQLite và dữ liệu mẫu; không cần Node để chạy ứng dụng. Trên Linux/macOS dùng `.venv/bin/python`.

| Vai trò | Tài khoản | Mật khẩu demo |
| --- | --- | --- |
| Thành viên | `member01`, `member02` | `Demo@123` |
| Kiểm duyệt | `moderator01` | `Demo@123` |
| Quản trị | `admin` | `Demo@123` |

Database mới có 12 mẫu skin, 8 vật phẩm trong hai kho đồ, hai tin bán và số dư giả lập. Các giá chỉ là dữ liệu bài tập, không phải báo giá thị trường.

## Chức năng và tài liệu

- Tra cứu/tìm skin theo tên, vũ khí, độ hiếm và wear; xem float, chi tiết.
- Kho đồ, đăng/hủy tin bán; mua bằng xu SC với chuyển quyền sở hữu.
- Đề nghị đổi skin, chấp nhận/từ chối/hủy; lịch sử và thông báo.
- Kiểm duyệt ẩn tin; admin sửa tài khoản và danh mục.
- [URD, SRS, API và biên bản bàn giao](docs/public).

Bản mặc định bật lỗi có chủ đích theo yêu cầu học phần. Bug Manifest và bằng chứng chi tiết nằm trong hồ sơ riêng cho giảng viên, không gửi cùng bộ tài liệu cho bạn cặp trước kiểm thử. `TRAINING_BUGS=0` là bản đối chiếu; tắt lỗi không sửa dữ liệu đã tạo trước đó.

```powershell
# PowerShell, dừng server cũ trước
$env:TRAINING_BUGS="0"
.venv\Scripts\python app.py
```

## Kiểm thử và triển khai

Test guard: `python -m unittest discover -s tests -v` với `TRAINING_BUGS=0`. Bộ chức năng mở rộng và tool API/UI/hiệu năng nằm trong `tools/`, `tooling/`; cần dependencies thử nghiệm riêng. Kết quả giữ nguyên PASS/FAIL thật, không biến lỗi dự kiến thành PASS.

VPS dùng Gunicorn + Nginx + systemd. Cấu hình cụ thể cho `student@192.168.2.211` trong `deploy/`; `bash deploy/install-vps.sh` giữ bản sao vhost cũ trước khi chuyển tên miền. Dịch vụ `shiloskin` tự khởi động cùng máy. Database/khóa phiên ở `instance/`, không đưa lên GitHub. Không dùng bản thực hành có lỗi và tài khoản mẫu cho giao dịch thật.

AI-assisted: Codex hỗ trợ thiết kế, mã nguồn, sinh tài liệu và thực thi công cụ; các báo cáo đính kèm bằng chứng thực chạy. Hai sinh viên cần đọc lại, xác nhận vai trò/chữ ký và chịu trách nhiệm nội dung trước khi nộp.
