# BIÊN BẢN BÀN GIAO SẢN PHẨM — MẪU 06 — CHƯA KÝ

Nguyễn Từ Lân – 23110306 · 25/10/2026 · ShiloSkin v1.0

## 0. Trạng thái biên bản
Biên bản bàn giao số1, bản dự thảo ngày25/10/2026. BÊN GIAO (chủ hệ thống theo phân công): Nguyễn Từ Lân – 23110306. BÊN NHẬN (tester theo phân công): Bùi Xuân Minh – 23110193. Hệ thống: ShiloSkin v1.0 — check metadata skin và giao dịch vật phẩm CS2 bằng SC mô phỏng.
Đây là hồ sơ để hai bên kiểm tra và ký nhận. Không tự xác nhận bên nhận đã tải đủ tài liệu/đăng nhập hoặc đã thực hiện kiểm thử chéo. Ngày ký chính thức, tag/hash bàn giao và kết quả kiểm tra liên kết cần ghi khi hai bên kiểm tra thật.

## I. Danh mục sản phẩm và tài liệu
| STT | Hạng mục | Đường dẫn/phiên bản | Trạng thái xác nhận |
| --- | --- | --- | --- |
| 1 | URD 1.0 | URD_23110306.md/.docx/.pdf | Đã soạn; bên nhận review, chưa ký |
| 2 | SRS1.0 | SRS_23110306.md/.docx/.pdf;16FR,10NFR | Chuẩn expected; chưa có phê duyệt độc lập |
| 3 | API1.0 theo Mẫu01 | Mau_01_Tai_lieu_API_23110306.md/.docx/.pdf | Tất cả route nghiệp vụ; cần bên nhận đối chiếu |
| 4 | Mã nguồn mirror | https://github.com/minhhal1180/shiloskin | Dùng tài khoản có quyền đẩy; xem README/deploy hiện hành |
| 5 | Repo gốc do người dùng cung cấp | https://github.com/lanzymez30/shiloskin | Ban đầu trống, tài khoản triển khai không có quyền push; không giả commit/chủ quyền |
| 6 | Ứng dụng HTTPS | https://sv21.bcse-vju.com | Địa chỉ bàn giao; xác nhận truy cập ở mụcII sau khi thử |
| 7 | Fixture demo mới | 12models,8inventory,2ACTIVElistings;4tài khoản/3roles | Số live có thể khác sau test; không reset chung khi chưa thống nhất |
| 8 | Công khai hỗ trợ AI | Codex hỗ trợ StudentCare và ShiloSkin | Không khẳng định kiểm thử mù/độc lập hoàn toàn |
### Tài khoản và dữ liệu thử
MEMBER: member01 (1000SC, item1..4), member02 (1500SC, item5..8). MODERATOR: moderator01. ADMIN: admin. Mật khẩu demo: Demo@123. Tin#1 item5 giá400SC; tin#2 item6 giá2200SC; item7/8 dành chọn đổi khi dataset mới. Dùng phiên trình duyệt riêng cho mỗi vai. Không sử dụng số dư/giá này cho giao dịch thật.

## II. Checklist do bên nhận trực tiếp kiểm tra
| Nội dung | Kết quả bên nhận | Thời điểm/ghi chú |
| --- | --- | --- |
| Mở được URL HTTPS | Chưa xác nhận trực tiếp | Bên nhận điền |
| Đăng nhập hai MEMBER, MODERATOR, ADMIN | Chưa xác nhận trực tiếp | Bên nhận điền |
| Nhận đủ URD/SRS/API, đọc được DOCX/PDF | Chưa xác nhận trực tiếp | Bên nhận điền |
| Đối chiếu fixture và cách tạo môi trường riêng | Chưa xác nhận trực tiếp | Bên nhận điền |
| Chốt tag/hash đang triển khai và thời gian giữ bản demo | Chưa xác nhận trực tiếp | Bên giao/bên nhận điền |
| Thống nhất lịch trao đổi/tiếp nhận bugreport | Chưa xác nhận trực tiếp | Hai bên điền |
Kiểm tra tự động hoặc thao tác của trợ lý không thay kết quả/chữ ký của bên nhận. Báo cáo thực thi phải phân biệt local và VPS, baseline và bản thực hành; không điền PASS cho các ô chỉ mới dự kiến.

## III. Giới hạn và nội dung không bàn giao cùng bộ công khai
Không Steam/tài sản/tiền thật; không đăng ký tài khoản; metadata và giá là demo; chưa có backup tự động hoặc cam kết SLA; trạng thái terminal không mở lại; chưa có hướng gắn tài sản Steam. NFR là mục tiêu kiểm chứng, không phải chứng nhận đã đạt.
Không gửi danh mục lỗi bố trí sẵn hoặc đáp án phát hiện lỗi trong bộ URD/SRS/API đưa cho người kiểm thử. Danh mục dành giảng viên được quản lý riêng. Việc cùng AI tham gia cả hai dự án phải khai báo; không thể hứa bí mật tuyệt đối hoặc tính mù hồi tố.

## IV. Cam kết dự kiến và xử lý bất đồng
Chủ hệ thống dự kiến duy trì link và phiên bản bàn giao đến buổi demo, phản hồi bugreport trong48giờ kể từ khi tiếp nhận; lịch thực hiện cần hai bên/giảng viên xác nhận. Giữ lỗi thực hành đến demo theo yêu cầu học phần, chỉ xử lý sự cố môi trường riêng và ghi rõ thay đổi.
Nếu expected result chưa rõ, đối chiếu FR/BR/NFR và lập mục hỏi lại trước khi chốt bug. Việc chưa ghi bất đồng không có nghĩa hai bên đồng ý toàn bộ. Mọi bổ sung yêu cầu phải tăng phiên bản hoặc lưu quyết định, không sửa âm thầm để đổi kết quả test đã ghi.

## V. Khai báo công cụ và ký nhận
Codex hỗ trợ tạo code, tài liệu, dữ liệu thử và bộ kiểm chứng cho cả StudentCare (Bùi Xuân Minh) và ShiloSkin (Nguyễn Từ Lân). Các sinh viên cần đọc lại, chạy đối chiếu, trực tiếp review và giải thích khi demo. Không sử dụng hỗ trợ AI để giả nhận xét, chữ ký hoặc kết quả kiểm thử chưa thực hiện.
BÊN GIAO: Nguyễn Từ Lân –23110306. Chữ ký: CHƯA KÝ. Ngày: CHỜ XÁC NHẬN.
BÊN NHẬN: Bùi Xuân Minh –23110193. Chữ ký: CHƯA KÝ. Ngày: CHỜ XÁC NHẬN.
Giảng viên/điều chỉnh sau kiểm tra: ĐỂ TRỐNG CHỜ NGƯỜI CÓ THẨM QUYỀN.
