# NGUỒN VÀ DANH MỤC HỒ SƠ CHỦ HỆ THỐNG

Nguyễn Từ Lân – 23110306 · 25/10/2026 · ShiloSkin v1.0

## Bộ tài liệu chủ hệ thống ShiloSkin
Chủ hệ thống theo cặp: Nguyễn Từ Lân – 23110306. Người nhận dự kiến: Bùi Xuân Minh – 23110193. Dự án: ShiloSkin v1.0, ứng dụng demo kiểm metadata skin và giao dịch CS2 bằng SC mô phỏng. Các file được soạn ở ba định dạng MD/DOCX/PDF:
| Tệp gốc | Nội dung | Phiên bản |
| --- | --- | --- |
| URD_23110306 | Bài toán, phạm vi, actor, ưu tiên, user stories,3luồng | 1.0 |
| SRS_23110306 | 16FR,10NFR,ma trận quyền,state,bảng quyết định,fixture | 1.0 |
| Mau_01_Tai_lieu_API_23110306 | Tất cả API thực tế, field/types/validation/response/errors | 1.0 |
| Mau_06_Bien_ban_ban_giao_1_23110306 | Lân giao sản phẩm/tài liệu cho Minh; chưa ký | Dự thảo1.0 |
## Nguồn và mức độ sử dụng mẫu
Nguồn biểu mẫu học phần là thư mục Drive https://drive.google.com/drive/folders/173jy7ytRCeVvkClLM5JoPLcjbKE2jT9Q. Bộ tham chiếu gồm9 tài liệu/mẫu được đọc qua chế độ xem công khai; file gốc bị hạn chế tải xuống. Các tài liệu này tái dựng cấu trúc cần nộp và điền nội dung của ShiloSkin, không tự nhận là bản sao xuất nguyên vẹn hoặc đã có chữ ký của người tạo mẫu. Mẫu01 cho API, mẫu06 cho biên bản; URD/SRS là đặc tả chủ hệ thống.
Mẫu02 Bug Manifest và tài liệu tester/mẫu03–05,biên bản2/chấm điểm thuộc bộ riêng do người có nhiệm vụ chuẩn bị; không chèn danh mục lỗi hoặc điểm giả vào public. Người chấm tự điền điểm/chữ ký.

## Nguồn bài toán và triển khai
Yêu cầu trực tiếp mới: thực hiện luôn app của Lân vì chưa tồn tại; app đơn giản để check skin/trading súng trên CS2. Các lựa chọn MEMBER/MODERATOR/ADMIN, SC mô phỏng,1:1,giới hạn dữ liệu và NFR được khai báo thành baseline1.0, chưa thay xác nhận phê duyệt của sinh viên/giảng viên.
Repo gốc được cung cấp https://github.com/lanzymez30/shiloskin ban đầu trống, tài khoản làm việc không có quyền push. Mirror triển khai: https://github.com/minhhal1180/shiloskin. Website: https://sv21.bcse-vju.com. Mô tả Hòa Lạc Food từng thấy trước khi triển khai không là nguồn yêu cầu của ShiloSkin; các ảnh khảo sát cũ chỉ là lịch sử môi trường, không đại diện sản phẩm mới.

## Tính trung thực và hỗ trợ AI
Codex hỗ trợ cả StudentCare và ShiloSkin; không khẳng định kiểm thử mù/độc lập hoàn toàn hoặc chữ ký của sinh viên. Mọi số đo trong báo cáo phải lấy bằng chứng thực thi, phân biệt local/live và chưa chạy/đã chạy. Tài liệu yêu cầu nêu expected behavior, không chứng nhận ứng dụng đang đạt toàn bộ tiêu chí. Bên nhận cần trực tiếp kiểm tra bộ hồ sơ trước khi ký biên bản.

## Tái tạo tài liệu
Chạy `python tools/build_owner_docs.py` từ checkout có module writer tại `../qlychtsv/tools/build_submission.py`, dependencies python-docx/reportlab/openpyxl và font Arial của Windows. Script đặt IDENTITY/PROJECT riêng và truyền đúng thư mục đầu ra; không gọi quy trình xây tài liệu StudentCare. Việc tái tạo không ký thay người dùng và không tạo số đo mới.
