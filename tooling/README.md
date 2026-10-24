# ShiloSkin — bộ công cụ kiểm thử

Chủ hệ thống: Nguyễn Từ Lân (23110306). Người thực thi: Bùi Xuân Minh (23110193). Bản ứng dụng này được xây dựng với AI hỗ trợ trong cùng phiên làm việc; kết quả không được mô tả là một đánh giá mù độc lập đối với phần mềm do bạn cặp tự phát triển.

API/UI và JMeter sử dụng database tạm cục bộ; không chạy tải lên VPS hoặc thay dữ liệu demo đang phục vụ. Assertion thất bại và ngưỡng không đạt được giữ nguyên trong JSON/HTML.

## API và giao diện

```powershell
npm.cmd --prefix tooling ci --ignore-scripts
python tooling/generate_postman.py
python tools/run_api_ui.py
```

Newman dùng `shiloskin.postman_collection.json`, environment và `postman-data.csv` với ba bộ dữ liệu. Phủ đăng nhập/phiên, danh mục/chi tiết, kho vật phẩm, tin đăng/tạo/hủy, trao đổi, lịch sử, thông báo và phân quyền. Có ca âm thiếu phiên, ID sai, tài nguyên không tồn tại, truy cập quản trị sai vai trò. HTML/JSON gốc ở `evidence/tooling/newman/`.

Puppeteer-core sử dụng Edge có sẵn. `ui-data.json` tách tài khoản và vật phẩm test khỏi script. Hai luồng: mua tin đăng và kiểm tra ví/quyền sở hữu; tạo đề nghị trao đổi, đối tác chấp nhận và kiểm tra hai chủ sở hữu. Ảnh và assertion ở `evidence/tooling/puppeteer/`. Các lỗi hiển thị hoặc nội dung vẫn làm assertion Fail dù backend chuyển trạng thái thành công.

`evidence/tooling/api-ui-summary.json` là metadata lần chạy riêng, không ghi đè metadata kết quả JMeter. Mã thoát 0 cho biết công cụ hoàn tất; Go/No-go phải căn cứ Pass/Fail và các yêu cầu, không suy từ mã thoát này.

## JMeter

`load.jmx` và `step.jmx` là native Apache JMeter. Chạy/đọc theo `tools/run_tooling.py`; kịch bản load 300 giây, step 1→2→4 người dùng, 120 giây/bậc, tải mục tiêu tối đa 3 request/giây. Các sampler đọc có xác thực, không phát sinh giao dịch. Đối chiếu ngưỡng theo SRS ShiloSkin, không dùng ngưỡng StudentCare.

Đọc file `.jtl`, HTML dashboard và JSON thực tế trong `evidence/tooling/jmeter-*`. `summarize_jmeter.py` tách chỉ số theo sampler và từng bậc; `capture-jmeter.cjs` chụp đồ thị từ chính dashboard Apache. Không suy ra điểm bão hòa hệ thống từ plateau do timer giới hạn tốc độ. Môi trường local WSGI/Windows không đại diện cho cấu hình hoặc mạng của VPS.
