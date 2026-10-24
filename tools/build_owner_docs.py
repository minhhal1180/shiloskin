"""Build ShiloSkin owner documents, without inventing acceptance or signatures."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/public"
OUT.mkdir(parents=True, exist_ok=True)
WRITER = ROOT.parent / "qlychtsv/tools/build_submission.py"
spec = importlib.util.spec_from_file_location("shared_document_writer", WRITER)
writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)
writer.IDENTITY = "Nguyễn Từ Lân – 23110306"
writer.PROJECT = "ShiloSkin v1.0"
writer.DAY = "25/10/2026"

OWNER = writer.IDENTITY
TESTER = "Bùi Xuân Minh – 23110193"
REPO = "https://github.com/minhhal1180/shiloskin"
ORIGINAL_REPO = "https://github.com/lanzymez30/shiloskin"
LIVE = "https://sv21.bcse-vju.com"
DRIVE = "https://drive.google.com/drive/folders/173jy7ytRCeVvkClLM5JoPLcjbKE2jT9Q"

FR = [
    ("FR-01", "Đăng nhập, phiên và đăng xuất", "MEMBER / MODERATOR / ADMIN", "US-01", "Tài khoản 1–80 ký tự sau trim; mật khẩu 1–200 ký tự, không chỉ khoảng trắng, giữ nguyên ký tự khi so hash. Tài khoản hoạt động và thông tin đúng được đăng nhập 200; sai, khóa hoặc không tồn tại dùng cùng lỗi 401. /me trả hồ sơ, vai trò, số dư và CSRF. Phiên tối đa 8 giờ; đăng xuất thu hồi phiên, cookie cũ bị 401."),
    ("FR-02", "Danh mục skin và bộ lọc", "Cả ba vai trò", "US-02", "GET /skins liệt kê 12 mẫu ban đầu; tìm chuỗi con theo tên HOẶC weapon bằng Unicode casefold; q tối đa 200 ký tự. Có bộ lọc weapon, rarity và wear. MEMBER/MODERATOR chỉ thấy mẫu active; ADMIN thấy cả mẫu ngừng hoạt động. rarity/wear ngoài enum trả 400; kết hợp bộ lọc theo AND."),
    ("FR-03", "Kiểm tra chi tiết skin", "Cả ba vai trò", "US-02", "Chi tiết theo ID hiển thị tên, loại súng trong trò chơi, độ hiếm, tình trạng, float, giá tham khảo bằng SC và trạng thái catalog. ID không tồn tại trả 404. Float là metadata demo do admin khai báo, không xác minh vật phẩm Steam hoặc giá thị trường thực. Mẫu ngừng hoạt động vẫn có thể xem chi tiết để giữ tham chiếu."),
    ("FR-04", "Kho vật phẩm và kiểm tra đối tác", "Cả ba vai trò đọc; MEMBER giao dịch", "US-03", "Kho mặc định của tài khoản; MEMBER có 4 vật phẩm ban đầu. Cho đọc metadata kho MEMBER khác qua user_id để chọn vật phẩm muốn đổi; đây là dữ liệu công khai của demo. Không lộ mật khẩu/khóa phiên. locked=true khi vật phẩm có tin ACTIVE. user_id không hợp lệ 400; MEMBER truy vấn người không phải MEMBER hoặc ID không tồn tại trả 404."),
    ("FR-05", "Tạo tin đăng bán", "MEMBER", "US-04", "Chỉ đăng vật phẩm đang thuộc mình, không có tin ACTIVE và mẫu còn active. item_id là số nguyên dương. Giá là số nguyên 1..100000 SC, không nhận boolean, số thập phân hoặc chuỗi không nguyên. Vật phẩm người khác 403; đã có tin ACTIVE 409; thành công 201, ACTIVE, có lịch sử và thông báo của người bán."),
    ("FR-06", "Hủy tin của mình", "MEMBER người bán", "US-04", "Chỉ người bán của tin ACTIVE được hủy, chuyển CANCELLED và mở khóa vật phẩm. Người khác 403; SOLD/HIDDEN/CANCELLED hoặc hủy lặp trả 409. Hủy không chuyển quyền sở hữu và không trả lại xu của giao dịch đã hoàn tất."),
    ("FR-07", "Mua bằng xu mô phỏng", "MEMBER người mua", "US-05", "Tin phải ACTIVE, người mua khác người bán và đủ SC. Chủ sở hữu item còn là seller hợp lệ, active và role MEMBER. Chỉ một người mua thành công: chuyển item, trừ người mua/cộng người bán đúng price và chuyển SOLD trong một giao dịch. Không tự mua hoặc thiếu xu: 409, không đổi dữ liệu. Ghi BUY và thông báo hai bên. Tin đã được đăng hợp lệ vẫn có thể bán khi mẫu catalog bị ẩn sau đó; catalog ngừng hoạt động chặn đăng mới, không thu hồi tin cũ trong MVP."),
    ("FR-08", "Gửi đề nghị đổi 1:1", "MEMBER người đề nghị", "US-06", "give_item_id thuộc mình; want_item_id thuộc MEMBER khác đang active. Hai ID khác nhau, hai item không nằm trong tin ACTIVE, hai mẫu catalog còn active. Thành công 201, PENDING, ghi lịch sử và thông báo người nhận. Tự đổi 400; cho item không thuộc mình 403; item bị khóa hoặc trùng cặp đề nghị PENDING 409. Đề nghị PENDING không giữ chỗ vật phẩm."),
    ("FR-09", "Chấp nhận và hoán đổi", "MEMBER người nhận", "US-06", "Chỉ recipient của PENDING được accept. Kiểm tra lại chủ của hai item, hai item chưa đăng bán, mẫu còn active và proposer còn active/role MEMBER. Sau đó hoán đổi owner atomically và chuyển ACCEPTED; không trao đổi SC. REJECTED/CANCELLED/ACCEPTED không thể accept lại: 409. Người không phải recipient: 403."),
    ("FR-10", "Từ chối hoặc rút đề nghị", "MEMBER liên quan", "US-06", "Recipient được reject PENDING → REJECTED; proposer được cancel PENDING → CANCELLED. Không đổi owner hay SC. Sai bên thao tác 403; xử lý lại trạng thái kết thúc 409. Có lịch sử và thông báo đối tác. Không có chức năng sửa hoặc mở lại đề nghị đã kết thúc."),
    ("FR-11", "Lịch sử hoạt động", "Cả ba vai trò", "US-07", "Người dùng chỉ đọc event mình là actor hoặc other_id; không phải nhật ký công khai toàn hệ thống. Có action, entity_type, entity_id, detail, actor và thời gian UTC. BUY, CREATE_LISTING, CANCEL_LISTING, CREATE_TRADE, TRADE_ACCEPTED/REJECTED/CANCELLED, MODERATE, CREATE_SKIN, UPDATE_SKIN, UPDATE_USER được ghi. Không cung cấp API sửa/xóa lịch sử."),
    ("FR-12", "Hồ sơ và số dư", "Cả ba vai trò", "US-01 / US-05", "GET /me trả id, username, name, role, balance nguyên. Balance là SC mô phỏng, không nạp/rút tiền; MEMBER01 ban đầu 1000, MEMBER02 1500, MODERATOR/ADMIN 0. Sau mua phải phản ánh số dư mới. Giao dịch chuẩn không tạo số dư âm; tổng SC hai bên được bảo toàn. Không có API sửa số dư tự do."),
    ("FR-13", "Kiểm duyệt ẩn tin", "MODERATOR", "US-08", "Chỉ MODERATOR được ẩn tin ACTIVE; reason 1..1000 ký tự sau trim bắt buộc. Chuyển HIDDEN, mở khóa vật phẩm, ghi MODERATE và báo người bán kèm lý do. Thiếu lý do 400; sai vai trò 403; tin không ACTIVE 409. MVP chưa có khôi phục HIDDEN; người bán có thể tạo tin mới nếu đáp ứng FR-05."),
    ("FR-14", "Quản trị tài khoản", "ADMIN", "US-09", "GET /users không trả hash; PATCH sửa name 1..120, role MEMBER/MODERATOR/ADMIN, active boolean. Không được tự khóa hoặc tự bỏ ADMIN. MEMBER còn tin ACTIVE hoặc đề nghị PENDING không được đổi sang role khác: 409. Khóa/đổi hồ sơ thu hồi phiên trước đó. Bản MVP cấp sẵn 4 tài khoản, chưa có đăng ký/tạo hoặc tự khôi phục mật khẩu."),
    ("FR-15", "Quản trị metadata skin", "ADMIN", "US-09", "Tạo/sửa tên và weapon 1..120 sau trim; rarity/wear thuộc enum; float_value hữu hạn trong [0,1]; reference_price nguyên 1..100000 SC, mặc định 100 khi tạo nếu bỏ qua; active boolean mặc định true. Tạo trả 201/id; sửa trả 200. Không xóa model có tham chiếu. Thay metadata không tự cấp thêm inventory."),
    ("FR-16", "Thông báo và đã đọc", "Cả ba vai trò", "US-07", "Chỉ đọc thông báo recipient_id hiện tại; có event, body, entity, thời điểm và is_read. POST /read chỉ của mình; sau tải lại is_read vẫn 1. ID người khác/không tồn tại 404. Tạo tin, mua/bán, đề nghị/xử lý đổi và kiểm duyệt phát thông báo sau nghiệp vụ thành công trong cùng transaction."),
]

NFR = [
    ("NFR-01", "Hiệu năng tìm skin", "GET /api/skins?q=...: p95 ≤800 ms, error <1%, tải thường 2 người dùng, ramp-up 10 giây, chạy 300 giây. Thử 1 người dùng dùng làm kiểm tra sơ bộ, không thay tải thường.", "JMeter/HTTP, nhận hết response body; không cộng thời gian định thời tải."),
    ("NFR-02", "Hiệu năng thông báo", "GET /api/notifications: p95 ≤900 ms, error <1%, 2 người dùng trong 300 giây, ramp-up 10 giây.", "JMeter/HTTP cùng kế hoạch tải thường; báo riêng login và business requests."),
    ("NFR-03", "Hiệu năng duyệt danh mục/tin", "GET /api/listings và GET /api/skins không q: p95 ≤1000 ms, error <1%, tăng bậc 1→2→4 người dùng; 120 giây/bậc, ramp-up 5 giây, timer nhóm giới hạn mục tiêu 3 request/giây.", "JMeter non-GUI, JTL + native dashboard; chưa suy rộng quá 4 người dùng."),
    ("NFR-04", "Bố cục có thể sử dụng", "375×812, 768×1024, 1366×768: hộp thoại nằm trong viewport, nhãn trạng thái và độ hiếm nhìn thấy; tên hợp lệ có khoảng cách không cắt im lặng trên desktop. Bảng có thể cuộn bên trong vùng riêng.", "Ảnh DOM/bounding box; kiểm các luồng thị trường, kho, đề nghị."),
    ("NFR-05", "Nội dung nhất quán", "ACCEPTED hiển thị Đã chấp nhận; tiền mô phỏng ghi SC, không ký hiệu USD; hướng dẫn float ghi 0..1. Nhãn phải khớp mã trạng thái API, không đổi thông điệp nghiệp vụ.", "Đối chiếu từ điển, DOM và JSON theo cùng entity."),
    ("NFR-06", "Bảo mật tối thiểu", "0 lần nghiệp vụ thành công trong ≥6 phép thử thiếu phiên/sai role/sai owner/thiếu CSRF; HTTPS; cookie Secure, HttpOnly, SameSite=Lax. Không lộ password/hash/token trong API công khai và báo cáo.", "API âm, cookie live HTTPS, kiểm quyền từng thao tác."),
    ("NFR-07", "Nhất quán và retry", "Mua/đổi cùng item đồng thời: tối đa 1 lần thành công; tổng SC bảo toàn khi mua; hoán đổi 2 owner trong một transaction. Retry cùng key/body trả kết quả cũ, không lặp chuyển SC/item/thông báo; khác body cùng key trả 409.", "Concurrent client và đọc lại inventory/balance/listing/trade; Idempotency-Key."),
    ("NFR-08", "Chịu đầu vào không hợp lệ", "GET /skins/ID không tồn tại →404; POST /listings với price='abc' →400, không trả 500. Sau lỗi /me và list vẫn 200; lỗi một request không dừng process.", "API âm và bước kiểm tra phục hồi ngay sau lỗi."),
    ("NFR-09", "Giới hạn dữ liệu", "Name/weapon 1..120 sau trim; float hữu hạn [0,1]; listing/reference price nguyên 1..100000; reason 1..1000; q ≤200; JSON request ≤1 MiB. Sai dữ liệu trả 400/413 và rollback, không ghi một phần.", "EP/BVA: 0/1/max/max+1, khoảng trắng, boolean, số không hữu hạn/sai kiểu."),
    ("NFR-10", "Truy vết bất biến", "100% BUY/TRADE/MODERATE và thao tác quản trị có actor, entity, chi tiết, timestamp. Chỉ các bên liên quan đọc history; không API sửa/xóa history. Sai nghiệp vụ không tạo event thành công.", "Đối chiếu event sau action và đọc route inventory; giữ raw evidence."),
]

US = [
    ("US-01", "Cả ba vai trò", "đăng nhập và biết vai trò/số dư", "sử dụng đúng quyền, thoát an toàn", "P0", "FR-01, FR-12"),
    ("US-02", "Thành viên", "tìm và xem metadata skin", "so sánh loại súng, float và giá tham khảo demo", "P0", "FR-02, FR-03"),
    ("US-03", "Thành viên", "xem kho của mình và kho công khai đối tác", "chọn đúng vật phẩm để đăng hoặc đề nghị đổi", "P0", "FR-04"),
    ("US-04", "Người bán", "đăng giá và hủy khi tin còn mở", "quản lý đề nghị bán của mình", "P0", "FR-05, FR-06"),
    ("US-05", "Người mua", "mua bằng SC mô phỏng", "nhận item, số dư và lịch sử chính xác", "P0", "FR-07, FR-12"),
    ("US-06", "Hai thành viên", "gửi, chấp nhận, từ chối hoặc rút đề nghị đổi 1:1", "đổi item bằng sự đồng ý của đúng hai bên", "P0", "FR-08, FR-09, FR-10"),
    ("US-07", "Cả ba vai trò", "xem lịch sử và thông báo của mình", "theo dõi kết quả, đánh dấu nội dung đã đọc", "P1", "FR-11, FR-16"),
    ("US-08", "Kiểm duyệt viên", "ẩn tin đang hoạt động kèm lý do", "ngăn tin cần xử lý tiếp tục giao dịch", "P1", "FR-13"),
    ("US-09", "Quản trị viên", "khóa/quản lý vai trò và catalog", "duy trì tài khoản, metadata dùng chung", "P1", "FR-14, FR-15"),
]


def table(headers, values):
    return writer.table(headers, values)


def save(stem, title, body):
    writer.write_document(stem, title, body, OUT)


def urd():
    body = f"""## 0. Kiểm soát tài liệu
Phiên bản URD 1.0, lập ngày 25/10/2026. Chủ hệ thống theo phân công cặp: {OWNER}. Người nhận dự kiến: {TESTER}. Trạng thái: baseline đề xuất để đọc, review và ký nhận; chưa có chữ ký phê duyệt của hai sinh viên/giảng viên.
Nguồn bài toán: người dùng yêu cầu thực hiện ứng dụng của Lân vì chưa tồn tại, là app đơn giản để check skin và trading súng trong CS2. Bối cảnh môn học và biểu mẫu lấy từ thư mục {DRIVE}. Không dùng mô tả của ứng dụng nhà hàng đang hiển thị trước đó trên domain để suy ra yêu cầu ShiloSkin.

## 1. Bài toán và mục tiêu
Người chơi trong bài tập cần xem metadata skin CS2, xem vật phẩm thuộc tài khoản demo, đặt tin bán, mua bằng xu mô phỏng và đề nghị đổi 1:1. Người kiểm duyệt cần ẩn tin kèm lý do; quản trị quản lý tài khoản và catalog. Mục tiêu MVP là hoàn chỉnh ba luồng mua, đổi và kiểm duyệt với quyền, trạng thái, lịch sử rõ ràng.
SC (Skin Credits) là số nguyên ảo, không có giá trị thanh toán, không nạp/rút hay đổi tiền. Từ “súng” trong dự án chỉ vật phẩm trong trò chơi CS2, không liên quan giao dịch vũ khí vật lý. Check skin là đọc thông tin metadata đã khai báo, không phải định giá thời gian thực hoặc xác minh tài sản Steam.

## 2. Phạm vi MVP
Trong phạm vi: tài khoản demo riêng, catalog/bộ lọc/chi tiết, kho metadata công khai, tin bán, mua bằng SC, đổi 1:1, lịch sử cá nhân, thông báo, kiểm duyệt, tài khoản và metadata. Dữ liệu bền vững bằng SQLite, giao diện web responsive và API JSON cùng domain.
Ngoài phạm vi: Steam/OpenID/API inventory, trade offer Steam thật, tiền pháp định, cổng thanh toán/nạp rút, ví crypto, xác minh giá thật, chat, đấu giá, escrow, vận chuyển hoặc mua bán vũ khí ngoài đời. Không hỗ trợ đăng ký tài khoản hoặc tự khôi phục mật khẩu trong MVP.

## 3. Actor và nhu cầu
""" + table(["Vai trò", "Mục tiêu", "Giới hạn"], [
        ("MEMBER", "Check skin, xem kho, đăng/mua, gửi/xử lý đề nghị đổi, lịch sử/thông báo", "Chỉ tác động item của mình và đề nghị liên quan; xem kho đối tác là đọc metadata"),
        ("MODERATOR", "Duyệt danh mục và ẩn tin ACTIVE có lý do; xem event của mình", "Không mua/bán/đổi, không quản lý tài khoản/cấp role"),
        ("ADMIN", "Quản lý hồ sơ/role/active và catalog skin", "Không tự khóa/bỏ quyền; không đóng vai MEMBER hoặc MODERATOR trên API nghiệp vụ"),
    ]) + """
## 4. User stories và ưu tiên
""" + table(["ID", "Là", "Tôi muốn", "Để", "Ưu tiên", "Truy vết"], US) + """
P0 là điều kiện có luồng sử dụng cốt lõi; P1 hoàn thiện quản trị và theo dõi trong cùng MVP. P1 không có nghĩa bỏ kiểm quyền hoặc bỏ lịch sử khi triển khai.

## 5. Ba luồng nghiệp vụ
### FLOW-01 — Đăng bán và mua bằng SC
1. Người bán đăng nhập, mở kho và chọn item chưa có tin ACTIVE.
2. Nhập giá nguyên 1..100000 SC; backend kiểm owner, catalog và khóa rồi tạo ACTIVE.
3. Người mua khác xem thị trường, kiểm metadata, giá và số dư.
4. Backend kiểm trạng thái, chủ hiện tại, tài khoản người bán, tự mua và đủ SC.
5. Trong một transaction: chuyển owner, trừ/cộng SC, ghi SOLD, BUY và thông báo.
6. Hai bên đọc lại kho, số dư và lịch sử. Nếu không hợp lệ, giao dịch bị từ chối và dữ liệu giữ nguyên.
7. Trước khi bán, seller có thể hủy ACTIVE → CANCELLED; sau SOLD không được hủy.

### FLOW-02 — Đề nghị đổi vật phẩm 1:1
1. Proposer chọn một item của mình và một item khác trong kho công khai của đối tác.
2. Backend kiểm hai owner, active và không có tin bán; chống trùng cặp PENDING.
3. Tạo PENDING, ghi lịch sử, thông báo recipient.
4. Recipient có thể reject; proposer có thể cancel trước khi xử lý.
5. Nếu recipient accept, backend kiểm lại owner và khóa tại thời điểm cập nhật.
6. Hoán đổi hai owner và ghi ACCEPTED trong cùng transaction; SC không đổi.
7. Thông báo đối tác và lưu lịch sử. Trạng thái kết thúc không được mở lại.

### FLOW-03 — Kiểm duyệt tin
1. MODERATOR đăng nhập và đọc danh sách tin.
2. Chọn một tin ACTIVE cần ẩn; nhập lý do 1..1000 ký tự.
3. Backend kiểm role, trạng thái và lý do tại API, không chỉ dựa vào nút UI.
4. Chuyển HIDDEN, mở khóa item, lưu MODERATE và thông báo người bán.
5. Thành viên không thể mua tin HIDDEN. Tin không được khôi phục trong MVP.

## 6. Quy tắc nghiệp vụ chính
Một inventory item có một owner và tối đa một tin ACTIVE. Tin SOLD không chuyển ngược thành CANCELLED. Mua phải khác seller và không làm số dư âm. Đổi cần đúng recipient chấp thuận khi PENDING; mọi quyền được kiểm lại phía server. PENDING không giữ chỗ, nên item thay đổi chủ hoặc được đăng bán trước lúc accept sẽ làm accept thất bại 409.
Các đơn vị, từ điển nội dung, ràng buộc số liệu và ngưỡng hiệu năng được cụ thể hóa trong SRS 1.0. Các giới hạn và chính sách là lựa chọn MVP cho đề bài đơn giản, không phải chính sách của Valve/Steam hoặc yêu cầu đã được giảng viên ký duyệt.

## 7. Điều kiện hoàn thành và truy vết
""" + table(["User story", "Chức năng", "Luồng", "Bằng chứng cần có"], [
        ("US-01", "FR-01, FR-12", "Tất cả", "Đăng nhập ba vai trò, hết phiên/đăng xuất, số dư"),
        ("US-02, US-03", "FR-02..04", "FLOW-01/02", "Filter/chi tiết và kho đúng metadata"),
        ("US-04, US-05", "FR-05..07", "FLOW-01", "State tin, owner, SC và rollback"),
        ("US-06", "FR-08..10", "FLOW-02", "Đúng người chấp thuận, hoán đổi và trạng thái kết thúc"),
        ("US-07", "FR-11, FR-16", "Tất cả", "History/notification riêng tư, read tồn tại sau refresh"),
        ("US-08, US-09", "FR-13..15", "FLOW-03/quản trị", "Lý do kiểm duyệt, RBAC, khóa và metadata"),
    ]) + f"""
Hoàn thành hồ sơ không đồng nghĩa nghiệm thu sản phẩm. Tester cần chạy testcase theo SRS; lỗi quan sát được được báo riêng và chưa được tự đánh dấu đã sửa. Chữ ký, xác nhận nhận đủ tài liệu và kết luận nghiệm thu do đúng người có trách nhiệm thực hiện.

## 8. Nguồn mã và công khai hỗ trợ AI
Repo người dùng cung cấp ban đầu: {ORIGINAL_REPO}, tại thời điểm khảo sát là repo trống; tài khoản đang làm việc không có quyền đẩy lên repo đó. Bản mirror dưới quyền triển khai: {REPO}; địa chỉ bàn giao: {LIVE}. Trạng thái kiểm chứng đường dẫn phải đọc trong biên bản/báo cáo thực thi, không suy từ việc tài liệu có ghi URL.
Codex hỗ trợ triển khai và soạn tài liệu cho cả StudentCare lẫn ShiloSkin theo yêu cầu trực tiếp. Vì cùng công cụ tham gia hai dự án, không tuyên bố kiểm thử mù hoặc độc lập hoàn toàn giữa hai người. Nguyễn Từ Lân và Bùi Xuân Minh cần đọc, chạy lại, xác nhận tài liệu và trực tiếp trao đổi khi bàn giao. Không giả chữ ký, nhận xét bạn cặp hoặc kết quả chưa chạy.
"""
    save("URD_23110306", "TÀI LIỆU YÊU CẦU NGƯỜI DÙNG — SHILOSKIN", body)


def srs():
    body = f"""## 0. Kiểm soát, mục đích và mức chuẩn tắc
SRS 1.0, chủ hệ thống {OWNER}, tham chiếu URD 1.0 và API 1.0 cùng bộ. Đây là baseline hành vi ĐÚNG để thiết kế testcase, có thể review và ký nhận; chưa có chữ ký phê duyệt. Bản thực hành có thể cố ý chứa sai lệch để học kiểm thử; không dùng sai lệch hiện tại làm expected result. Danh mục lỗi bố trí riêng không nằm trong bộ bàn giao công khai này.

## 1. Kiến trúc và môi trường
Một web app Flask/SQLite, HTML/CSS/JavaScript, API JSON cùng domain. Server triển khai bằng WSGI/Gunicorn sau Nginx/HTTPS của lab; môi trường cục bộ dùng Python 3.11+ với server thử nghiệm. Phiên cookie ký số, mật khẩu hash scrypt, CSRF trên API ghi dữ liệu.
Không kết nối Steam, không thanh toán hoặc giao dịch tài sản thật. SC là credit mô phỏng nguyên. Giá tham khảo của skin là metadata bài tập, không phải khuyến nghị mua bán hay dữ liệu thị trường.

## 2. Thuật ngữ và dữ liệu
Skin/model là catalog metadata; inventory item là bản ghi vật phẩm có một owner. Listing là tin đăng bán item; trade là đề nghị đổi hai item. Proposer gửi đề nghị, recipient là owner của item được muốn đổi tại thời điểm tạo.
""" + table(["Entity", "Thuộc tính nghiệp vụ", "Ràng buộc chính"], [
        ("User", "id, username, name, password_hash, role, active, balance, session_version", "3 role; balance nguyên SC; không trả password_hash"),
        ("Skin", "id, name, weapon, rarity, wear, float_value, reference_price, active, timestamps", "Name/weapon 1..120; float hữu hạn 0..1; price 1..100000"),
        ("Inventory", "id, skin_id, owner_id, acquired_at", "Một owner; locked được tính từ tin ACTIVE"),
        ("Listing", "id, item_id, seller_id, buyer_id, price, status, moderation_reason, timestamps", "Tối đa một ACTIVE/item; SOLD chỉ một buyer"),
        ("Trade", "id, proposer_id, recipient_id, give_item_id, want_item_id, status, timestamps", "1:1, không tự đổi, không lặp cặp PENDING"),
        ("History", "actor_id, other_id, action, entity_type/id, detail, created_at", "Chỉ các bên liên quan đọc; bất biến"),
        ("Notification", "recipient_id, event_type, body, entity_type/id, is_read, created_at", "Chỉ người nhận; is_read bền vững"),
        ("Idempotency", "user, method, path, key, digest, response/status", "Cùng thao tác retry không chạy lại tác động"),
    ]) + """
Rarity: Consumer Grade, Industrial Grade, Mil-Spec, Restricted, Classified, Covert. Wear: Factory New, Minimal Wear, Field-Tested, Well-Worn, Battle-Scarred. Đây là enum khai báo của demo; app không tự suy wear từ float hoặc xác minh metadata với nhà phát hành.
Timestamps API dùng ISO8601 UTC. Name/weapon/reason/username được trim; mật khẩu được kiểm không trống nhưng không trim trước so hash. Query casefold, không tự bỏ dấu. Trường boolean phải là boolean JSON; ID nguyên dương, boolean không được coi là số.

## 3. Yêu cầu chức năng
"""
    for identifier, title, actor, story, rule in FR:
        body += f"### {identifier} — {title}\nActor: {actor}. Truy vết: {story}.\n{rule}\n"
    body += """
## 4. Ma trận quyền API
""" + table(["Nhóm thao tác", "MEMBER", "MODERATOR", "ADMIN"], [
        ("Login/logout/me, catalog/chi tiết", "Có", "Có", "Có"),
        ("Xem metadata kho MEMBER", "Có", "Có", "Có"),
        ("Đọc danh sách tin", "Có", "Có", "Có"),
        ("Đăng/hủy tin", "Item/tin của mình, đúng state", "Không", "Không"),
        ("Mua tin", "Tin người khác, đúng state và đủ SC", "Không", "Không"),
        ("Gửi/xem đề nghị đổi", "Chỉ các đề nghị liên quan", "Không", "Không"),
        ("Accept/reject", "Đúng recipient PENDING", "Không", "Không"),
        ("Cancel đề nghị", "Đúng proposer PENDING", "Không", "Không"),
        ("Ẩn tin", "Không", "ACTIVE + lý do", "Không"),
        ("Danh sách/sửa tài khoản", "Không", "Không", "Có, có bảo vệ self/role change"),
        ("Tạo/sửa catalog", "Không", "Không", "Có"),
        ("History/notification", "Chỉ liên quan/chỉ của mình", "Chỉ liên quan/chỉ của mình", "Chỉ liên quan/chỉ của mình"),
    ]) + """
Mọi ghi dữ liệu sau login yêu cầu phiên hợp lệ và X-CSRF-Token trước khi chạy nghiệp vụ. UI ẩn nút không thay phân quyền server. Tài khoản inactive hoặc session_version đổi bị thu hồi phiên. Đăng xuất chủ ý thu hồi mọi cookie phiên của tài khoản đó trong MVP.

## 5. Vòng đời và chuyển trạng thái
### 5.1. Tin đăng
```
ACTIVE -- seller cancel --> CANCELLED
ACTIVE -- other member buys atomically --> SOLD
ACTIVE -- moderator reason --> HIDDEN
```
SOLD, CANCELLED và HIDDEN là trạng thái kết thúc của tin. Chủ item có thể đăng một tin mới nếu không còn ACTIVE; tin cũ không được mở lại. Sau SOLD owner item là buyer; seller cũ không được tác động item chỉ vì vẫn là seller của hồ sơ tin cũ.
### 5.2. Đề nghị đổi
```
PENDING -- recipient accepts + recheck both items --> ACCEPTED
PENDING -- recipient rejects --> REJECTED
PENDING -- proposer cancels --> CANCELLED
```
Không có cạnh từ trạng thái kết thúc về PENDING/ACCEPTED. PENDING không khóa item; vì vậy thay owner hoặc đăng item vào ACTIVE trước thời điểm accept làm accept thất bại 409 và giữ đề nghị chờ để các bên từ chối/hủy.

## 6. Bảng quyết định
### 6.1. Quyết định mua
""" + table(["Điều kiện", "Trường hợp A", "B", "C", "D", "E"], [
        ("Vai trò MEMBER", "Không", "Có", "Có", "Có", "Có"),
        ("Tin ACTIVE/chủ hợp lệ", "—", "Không", "Có", "Có", "Có"),
        ("Buyer khác seller", "—", "—", "Không", "Có", "Có"),
        ("Đủ số dư", "—", "—", "—", "Không", "Có"),
        ("Kết quả", "403", "409", "409", "409", "200 + một transfer/SOLD"),
    ]) + """
### 6.2. Quyết định chấp nhận đổi
""" + table(["Điều kiện", "K1", "K2", "K3", "K4"], [
        ("Đúng recipient MEMBER", "Không", "Có", "Có", "Có"),
        ("State PENDING", "—", "Không", "Có", "Có"),
        ("Hai item/owner/active/khóa còn hợp lệ", "—", "—", "Không", "Có"),
        ("Kết quả", "403", "409", "409, không swap", "200 + swap/ACCEPTED"),
    ]) + """
## 7. Validation và lỗi
Input sai kiểu, trống, ngoài khoảng hoặc action không thuộc enum →400; chưa đăng nhập/hết phiên/khóa →401; sai quyền hoặc CSRF →403; entity thiếu →404; trùng/chuyển state xung đột →409; body quá lớn →413. Response lỗi JSON có trường error, không xuất traceback/mật khẩu. HTTP500 là lỗi hệ thống, không được dùng thay validation/not-found trong các NFR đã định.
Nếu transaction lỗi, rollback mọi thay đổi của thao tác đó. Không trả success khi chưa commit; không tự hoàn tiền hoặc đảo item sau khi một giao dịch đã được xác nhận hoàn tất bằng API khác.

## 8. Yêu cầu phi chức năng và cách đo
""" + table(["ID", "Tên", "Ngưỡng/tiêu chí", "Phương pháp"], NFR) + """
### 8.1. Fixture và giới hạn tải
Fixture khởi tạo mới: 12 skin model, 8 inventory item, 2 tin ACTIVE, 4 tài khoản (2 MEMBER + 1 MODERATOR + 1 ADMIN). member01 có item 1..4; member02 có item 5..8; tin #1 item5 giá400SC, tin #2 item6 giá2200SC. Kho đối tác item7/8 chưa đăng là dữ liệu đổi thử. Kết quả test phải dùng fixture riêng, không reset dữ liệu live chung.
Trước khi đo tải, ghi lại số model/item/tin sau các bước setup; tối đa 20 model cho kế hoạch này. Nếu có setup thêm catalog/item thì báo số thực, không giữ nhãn “12/8/2” khi dữ liệu đã đổi. Tải cục bộ cùng server/tool không đại diện năng lực VPS. Chỉ tải GET đã nêu, không vượt 4 người dùng hoặc giới hạn mục tiêu 3 request/s của step test. Chưa có phép ngoại suy bão hòa, stress không giới hạn hay đo trên hạ tầng dùng chung ngoài khung giờ cho phép.

## 9. Truy vết và thiết kế kiểm thử
""" + table(["Luồng", "FR", "NFR trọng yếu", "Kỹ thuật cần phủ"], [
        ("FLOW-01 mua", "01..07, 11, 12, 16", "06,07,09,10", "EP/BVA giá, bảng quyết định đủ SC/tự mua, state tin, retry/concurrency"),
        ("FLOW-02 đổi", "01,03,04,08..12,16", "06,07,09,10", "Owner × role × state, swap atomic, đối tác kết thúc, E2E"),
        ("FLOW-03 kiểm duyệt", "01,02,03,11,13,16", "04,05,06,09,10", "Reason BVA, role, ACTIVE/HIDDEN, thông báo"),
        ("Quản trị", "14,15", "06,08,09,10", "Tài khoản khóa, không tự khóa, float biên, enum, lỗi JSON"),
        ("Hiệu năng/nội dung/UI", "02,03,04,07,09,16", "01..05,08", "Đúng dataset/viewports, HTTP timing, ảnh cùng entity"),
    ]) + f"""
## 10. Hạn chế và lựa chọn cần được review
Baseline dùng cấp sẵn tài khoản, không đăng ký hoặc thêm inventory từ Steam; 1 item/1 listing, đổi 1:1 không bù SC; giá tham khảo thủ công; không auto hủy các đề nghị PENDING khi item thay đổi; inactive catalog không tự thu hồi tin đang bán; không có khôi phục tin HIDDEN. Những lựa chọn này là phạm vi MVP được khai báo, không tự gán thành lỗi ngoài đặc tả hoặc tính năng đã được yêu cầu trong đề gốc.
Các mục NFR là mục tiêu chuẩn tắc của bản yêu cầu, không phải báo cáo đã đạt. Tình trạng thực đo, lỗi và phần chưa chạy phải lấy từ báo cáo thực thi; bản này không mạo danh xác nhận của {TESTER}. AI hỗ trợ cả hai ứng dụng; cần khai báo cùng báo cáo và không khẳng định blind test.
"""
    save("SRS_23110306", "ĐẶC TẢ YÊU CẦU PHẦN MỀM — SHILOSKIN", body)


def api_doc():
    endpoints = [
        ("POST", "/login", "Không cần phiên", "FR-01", "{username:string1..80,password:string1..200}", "200 {ok:true}; cookie phiên. Sai thông tin/khóa:401."),
        ("POST", "/logout", "Cả ba vai trò + CSRF", "FR-01", "{}", "200 {ok:true}; thu hồi phiên; cookie cũ gọi /me:401."),
        ("GET", "/me", "Có phiên", "FR-01,12", "Không body", "200 {user:{id,username,name,role,balance},csrf:string}. Không trả hash."),
        ("GET", "/skins", "Có phiên", "FR-02", "?q=Redline&weapon=AK-47&rarity=Classified&wear=Field-Tested; q≤200", "200 {items:Skin[],rarities:string[],wears:string[]}; enum filter sai:400."),
        ("GET", "/skins/:id", "Có phiên", "FR-03", "Path id nguyên không âm theo route; dùng ID dương trong client", "200 {item:Skin}; không tồn tại:404."),
        ("GET", "/inventory", "Có phiên", "FR-04", "?user_id=2; bỏ qua để xem kho mình", "200 {items:InventoryItem[],owner:{id,name,username}|null,users:[{id,name,username}]}; user_id sai:400/404 theo FR-04."),
        ("GET", "/listings", "Có phiên", "FR-05..07,13", "?q=Glock&status=ACTIVE&mine=1; status ACTIVE/SOLD/CANCELLED/HIDDEN", "200 {items:Listing[]}; mặc định gồm mọi trạng thái; mine=1 lọc seller hiện tại; q≤200."),
        ("POST", "/listings", "MEMBER + CSRF", "FR-05", "{item_id:positiveInteger,price:integer1..100000}", "201 {id}; item người khác:403; khóa/inactive:409; giá sai:400."),
        ("POST", "/listings/:id/cancel", "MEMBER seller + CSRF", "FR-06", "{}", "200 {ok:true}; không phải seller:403; không ACTIVE:409."),
        ("POST", "/listings/:id/buy", "MEMBER buyer + CSRF", "FR-07,12", "{}", "200 {ok:true,balance:integer}; tự mua/thiếu SC/tin đã kết thúc/chủ thay đổi:409."),
        ("POST", "/listings/:id/moderate", "MODERATOR + CSRF", "FR-13", "{reason:string1..1000 sau trim}", "200 {ok:true}; rỗng:400; sai role:403; không ACTIVE:409."),
        ("GET", "/trades", "MEMBER", "FR-08..10", "Không body", "200 {items:Trade[]}; chỉ proposer/recipient hiện tại, không toàn hệ thống."),
        ("POST", "/trades", "MEMBER + CSRF", "FR-08", "{give_item_id:positiveInteger,want_item_id:positiveInteger}", "201 {id}; sai owner give:403; tự đổi:400; khóa/trùng pending/đối tác không hợp lệ:409."),
        ("POST", "/trades/:id/action", "MEMBER đúng bên + CSRF", "FR-09,10", "{action:'accept'|'reject'|'cancel'}", "200 {ok:true,status}; accept/reject chỉ recipient, cancel chỉ proposer; sai bên403; state xung đột409."),
        ("GET", "/history", "Có phiên", "FR-11", "Không body", "200 {items:HistoryEvent[]}; actor hoặc other_id hiện tại; không API update/delete."),
        ("GET", "/notifications", "Có phiên", "FR-16", "Không body", "200 {items:Notification[]}; chỉ recipient hiện tại."),
        ("POST", "/notifications/:id/read", "Người nhận + CSRF", "FR-16", "{}", "200 {ok:true}; is_read=1 bền vững; ID thiếu/của người khác:404."),
        ("GET", "/users", "ADMIN", "FR-14", "Không body", "200 {items:UserAdmin[]}; không password_hash/session_version."),
        ("PATCH", "/users/:id", "ADMIN + CSRF", "FR-14", "{name?:string1..120,role?:MEMBER|MODERATOR|ADMIN,active?:boolean}", "200 {ok:true}; self khóa/bỏ admin400; role change đang có tin/đề nghị409; thu hồi phiên cũ."),
        ("POST", "/skins", "ADMIN + CSRF", "FR-15", "{name,weapon,rarity,wear,float_value,reference_price?:integer,active?:boolean}", "201 {id}; name/weapon1..120, enum hợp lệ, float finite0..1, reference_price1..100000 default100, active defaulttrue."),
        ("PATCH", "/skins/:id", "ADMIN + CSRF", "FR-15", "Bất kỳ trường hợp lệ của POST /skins; trường bỏ qua giữ giá trị cũ", "200 {ok:true}; ID thiếu404; sai field400. Không tự tạo inventory."),
    ]
    body = f"""## 0. Phạm vi và phiên bản
API 1.0 cho ShiloSkin v1.0. Base URL triển khai: {LIVE}/api; cục bộ mặc định http://127.0.0.1:5001/api. Mọi ví dụ dưới đây là dữ liệu demo minh họa contract, không phải số đo/response đã chạy ở VPS. Các route mô tả đúng API của baseline; lỗi quan sát trong bản thực hành phải được báo riêng.
Repo mirror: {REPO}; tài liệu SRS_23110306 là nguồn expected behavior. Không tích hợp Steam hoặc thanh toán; tất cả price, reference_price, balance đều là SC nguyên.

## 1. Xác thực và CSRF
POST /login JSON username/password tạo cookie phiên tối đa 8 giờ. Sau login, GET /me lấy user và csrf. Mọi POST/PATCH sau login bắt buộc cookie và header X-CSRF-Token. Không đặt password hoặc CSRF vào URL/log/tài liệu bằng chứng. Cookie HTTPS triển khai phải Secure/HttpOnly/SameSite=Lax; localhost không bật Secure.
Đăng xuất hoặc admin sửa tài khoản làm cookie phiên cũ bị từ chối. API kiểm role/owner/state phía server, không phụ thuộc việc nút đã bị ẩn trên UI.

## 2. Quy ước dữ liệu và response
Request ghi dùng Content-Type: application/json, object JSON. Không hỗ trợ upload/Steam URL trong MVP. Thành công tạo mới trả201 {{id}}, cập nhật200 {{ok:true}}; GET danh sách có items và chi tiết có item. Timestamps ISO8601 UTC; id là số nguyên; active/is_read phản ánh dữ liệu boolean/0..1 theo schema. Body request tối đa1MiB; JSON lớn hơn trả413.
Name/weapon/reason/username trim. Password giữ nguyên khi so hash. Integer không nhận boolean hoặc số thập phân; float phải hữu hạn. Field không được API hỗ trợ không có tác động nghiệp vụ; client chỉ nên gửi field đã mô tả. Không có phân trang trên bộ dữ liệu nhỏ MVP.

## 3. Kiểu dữ liệu trả về
""" + table(["Type", "Các trường"], [
        ("Skin", "id:int, name/weapon/rarity/wear:string, float_value:number, reference_price:int SC, active:0/1, created_at/updated_at:ISO8601"),
        ("InventoryItem", "id/item_id:int, skin_id:int, owner_id:int, owner_name/skin_name/weapon/rarity/wear:string, float_value:number, reference_price:int, acquired_at:time, locked:boolean"),
        ("Listing", "id/item_id/skin_id/seller_id:int, buyer_id:int|null, seller_name:string, buyer_name:string|null, price:int, status, moderation_reason, skin metadata, timestamps"),
        ("Trade", "id/proposer_id/recipient_id/give_item_id/want_item_id:int, proposer_name/recipient_name/give_skin_name/want_skin_name:string, status, timestamps"),
        ("HistoryEvent", "id/actor_id/entity_id:int, other_id:int|null, actor_name/action/entity_type/detail:string, created_at:time"),
        ("Notification", "id/recipient_id/entity_id:int, event_type/body/entity_type:string, is_read:0/1, created_at:time"),
        ("UserAdmin", "id:int, username/name/role:string, active:0/1, balance:int SC"),
    ]) + """
Listing statuses: ACTIVE, SOLD, CANCELLED, HIDDEN. Trade statuses: PENDING, ACCEPTED, REJECTED, CANCELLED. Rarity/wear enums xem SRS mục2. /listings công khai theo quyền đọc có lịch sử trạng thái; UI thị trường phải chủ động dùng status=ACTIVE khi muốn chỉ hiển thị tin mua được.

## 4. Danh mục đầy đủ endpoint
""" + table(["Method", "Path sau /api", "Quyền", "Truy vết", "Đầu vào", "Response/exception"], endpoints) + """
## 5. Ví dụ quy trình có thể thử trên database demo mới
### 5.1. Đăng nhập, kiểm số dư và mua
POST /login với {"username":"member01","password":"Demo@123"}. GET /me lấy csrf. GET /listings?status=ACTIVE: demo mới có tin#1 item5 giá400SC và tin#2 item6 giá2200SC. POST /listings/1/buy gửi {} với cookie/CSRF sẽ chuyển item5 từ member02 sang member01, số dư member01 từ1000 còn600 trong baseline. Đây là ví dụ theo fixture, không khẳng định dữ liệu live hiện chưa bị người khác test.
### 5.2. Đổi 1:1
Member01 POST /trades {"give_item_id":1,"want_item_id":7}. Member02 đăng nhập bằng context/cookie riêng, GET /trades lấy id rồi POST /trades/:id/action {"action":"accept"}. Baseline chuyển item1 sang member02, item7 sang member01, status ACCEPTED và SC không đổi. Dùng database mới hoặc kiểm lại owner/item trước khi lặp ví dụ.
### 5.3. Kiểm duyệt
Moderator01 POST /listings/1/moderate {"reason":"Cần kiểm tra mô tả vật phẩm"}. Nếu tin#1 vẫn ACTIVE thì baseline trả200, HIDDEN; nếu người khác đã mua/hủy, trả409. Chỉ MODERATOR được phép, ADMIN không thay vai trò này trên API.

## 6. Mã lỗi
""" + table(["HTTP", "Ý nghĩa", "Ví dụ baseline"], [
        (400, "Validation", "price=0/100001/'abc', float=-0.01/1.01, name trống, reason trống, enum/action sai"),
        (401, "Không có phiên hợp lệ", "Sai password, tài khoản khóa, session hết hạn/đã logout"),
        (403, "Sai quyền/owner/CSRF", "MEMBER gọi /users; seller hủy tin người khác; proposer accept trade; thiếu token"),
        (404, "Không có entity hoặc không thuộc tập được thấy", "Skin/listing/trade ID thiếu; notification người khác"),
        (405, "Method không được route hỗ trợ", "PATCH /history hoặc DELETE /notifications"),
        (409, "Xung đột state/điều kiện", "Tự mua, thiếu SC, mua SOLD, accept REJECTED, hai giao dịch cạnh tranh, item locked"),
        (413, "Body quá lớn", "JSON vượt1MiB"),
        (500, "Lỗi hệ thống", "Không là expected cho input/ID thiếu ở NFR-08; kiểm tra /me/list tiếp sau để xác nhận process còn sống"),
    ]) + """
Error JSON có dạng {"error":"Thông báo tiếng Việt"}; không đưa traceback. Các validation được thực hiện trong transaction, lỗi không để lại item/balance/trade bị thay đổi một phần.

## 7. Retry và đồng thời
Client có thể gửi Idempotency-Key tối đa100ký tự cho POST/PATCH sau login. Cùng user/method/path/key và cùng raw body trả response đã lưu, không tái chạy nghiệp vụ. Cùng key nhưng body khác trả409. Mỗi thao tác mới dùng key mới. Chưa có lịch tự dọn bảng key trong MVP. Chưa cung cấp key hoặc thay key không được coi là retry cùng thao tác; state/unique constraint vẫn ngăn chuyển một item hai lần.
SQLite BEGIN IMMEDIATE bao quanh thao tác ghi, khóa ngắn và điều kiện state/owner bảo vệ mua và đổi. Hai request cạnh tranh phải đọc lại dữ liệu đã commit của request trước. Không giả lập swap bằng hai lời gọi API độc lập.

## 8. Tài khoản demo và trách nhiệm
member01/member02: MEMBER; moderator01: MODERATOR; admin: ADMIN; mật khẩu demo chung Demo@123. Dùng context/incognito khác nhau khi thử hai bên. Không gửi dữ liệu cá nhân hoặc tài sản thật. Chủ hệ thống và tester cần tự đối chiếu contract trước khi ký; Codex hỗ trợ cả hai ứng dụng, không thay thế kiểm thử chéo và xác nhận của sinh viên.
"""
    save("Mau_01_Tai_lieu_API_23110306", "TÀI LIỆU API — MẪU 01 — SHILOSKIN", body)


def handover():
    body = f"""## 0. Trạng thái biên bản
Biên bản bàn giao số1, bản dự thảo ngày25/10/2026. BÊN GIAO (chủ hệ thống theo phân công): {OWNER}. BÊN NHẬN (tester theo phân công): {TESTER}. Hệ thống: ShiloSkin v1.0 — check metadata skin và giao dịch vật phẩm CS2 bằng SC mô phỏng.
Đây là hồ sơ để hai bên kiểm tra và ký nhận. Không tự xác nhận bên nhận đã tải đủ tài liệu/đăng nhập hoặc đã thực hiện kiểm thử chéo. Ngày ký chính thức, tag/hash bàn giao và kết quả kiểm tra liên kết cần ghi khi hai bên kiểm tra thật.

## I. Danh mục sản phẩm và tài liệu
""" + table(["STT", "Hạng mục", "Đường dẫn/phiên bản", "Trạng thái xác nhận"], [
        (1, "URD1.0", "URD_23110306.md/.docx/.pdf", "Đã soạn; bên nhận review, chưa ký"),
        (2, "SRS1.0", "SRS_23110306.md/.docx/.pdf;16FR,10NFR", "Chuẩn expected; chưa có phê duyệt độc lập"),
        (3, "API1.0 theo Mẫu01", "Mau_01_Tai_lieu_API_23110306.md/.docx/.pdf", "Tất cả route nghiệp vụ; cần bên nhận đối chiếu"),
        (4, "Mã nguồn mirror", REPO, "Dùng tài khoản có quyền đẩy; xem README/deploy hiện hành"),
        (5, "Repo gốc do người dùng cung cấp", ORIGINAL_REPO, "Ban đầu trống, tài khoản triển khai không có quyền push; không giả commit/chủ quyền"),
        (6, "Ứng dụng HTTPS", LIVE, "Địa chỉ bàn giao; xác nhận truy cập ở mụcII sau khi thử"),
        (7, "Fixture demo mới", "12models,8inventory,2ACTIVElistings;4tài khoản/3roles", "Số live có thể khác sau test; không reset chung khi chưa thống nhất"),
        (8, "Công khai hỗ trợ AI", "Codex hỗ trợ StudentCare và ShiloSkin", "Không khẳng định kiểm thử mù/độc lập hoàn toàn"),
    ]) + """
### Tài khoản và dữ liệu thử
MEMBER: member01 (1000SC, item1..4), member02 (1500SC, item5..8). MODERATOR: moderator01. ADMIN: admin. Mật khẩu demo: Demo@123. Tin#1 item5 giá400SC; tin#2 item6 giá2200SC; item7/8 dành chọn đổi khi dataset mới. Dùng phiên trình duyệt riêng cho mỗi vai. Không sử dụng số dư/giá này cho giao dịch thật.

## II. Checklist do bên nhận trực tiếp kiểm tra
""" + table(["Nội dung", "Kết quả bên nhận", "Thời điểm/ghi chú"], [
        ("Mở được URL HTTPS", "Chưa xác nhận trực tiếp", "Bên nhận điền"),
        ("Đăng nhập hai MEMBER, MODERATOR, ADMIN", "Chưa xác nhận trực tiếp", "Bên nhận điền"),
        ("Nhận đủ URD/SRS/API, đọc được DOCX/PDF", "Chưa xác nhận trực tiếp", "Bên nhận điền"),
        ("Đối chiếu fixture và cách tạo môi trường riêng", "Chưa xác nhận trực tiếp", "Bên nhận điền"),
        ("Chốt tag/hash đang triển khai và thời gian giữ bản demo", "Chưa xác nhận trực tiếp", "Bên giao/bên nhận điền"),
        ("Thống nhất lịch trao đổi/tiếp nhận bugreport", "Chưa xác nhận trực tiếp", "Hai bên điền"),
    ]) + """
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
"""
    save("Mau_06_Bien_ban_ban_giao_1_23110306", "BIÊN BẢN BÀN GIAO SẢN PHẨM — MẪU 06 — CHƯA KÝ", body)


def provenance():
    body = f"""## Bộ tài liệu chủ hệ thống ShiloSkin
Chủ hệ thống theo cặp: {OWNER}. Người nhận dự kiến: {TESTER}. Dự án: ShiloSkin v1.0, ứng dụng demo kiểm metadata skin và giao dịch CS2 bằng SC mô phỏng. Các file được soạn ở ba định dạng MD/DOCX/PDF:
""" + table(["Tệp gốc", "Nội dung", "Phiên bản"], [
        ("URD_23110306", "Bài toán, phạm vi, actor, ưu tiên, user stories,3luồng", "1.0"),
        ("SRS_23110306", "16FR,10NFR,ma trận quyền,state,bảng quyết định,fixture", "1.0"),
        ("Mau_01_Tai_lieu_API_23110306", "Tất cả API thực tế, field/types/validation/response/errors", "1.0"),
        ("Mau_06_Bien_ban_ban_giao_1_23110306", "Lân giao sản phẩm/tài liệu cho Minh; chưa ký", "Dự thảo1.0"),
    ]) + f"""
## Nguồn và mức độ sử dụng mẫu
Nguồn biểu mẫu học phần là thư mục Drive {DRIVE}. Bộ tham chiếu gồm9 tài liệu/mẫu được đọc qua chế độ xem công khai; file gốc bị hạn chế tải xuống. Các tài liệu này tái dựng cấu trúc cần nộp và điền nội dung của ShiloSkin, không tự nhận là bản sao xuất nguyên vẹn hoặc đã có chữ ký của người tạo mẫu. Mẫu01 cho API, mẫu06 cho biên bản; URD/SRS là đặc tả chủ hệ thống.
Mẫu02 Bug Manifest và tài liệu tester/mẫu03–05,biên bản2/chấm điểm thuộc bộ riêng do người có nhiệm vụ chuẩn bị; không chèn danh mục lỗi hoặc điểm giả vào public. Người chấm tự điền điểm/chữ ký.

## Nguồn bài toán và triển khai
Yêu cầu trực tiếp mới: thực hiện luôn app của Lân vì chưa tồn tại; app đơn giản để check skin/trading súng trên CS2. Các lựa chọn MEMBER/MODERATOR/ADMIN, SC mô phỏng,1:1,giới hạn dữ liệu và NFR được khai báo thành baseline1.0, chưa thay xác nhận phê duyệt của sinh viên/giảng viên.
Repo gốc được cung cấp {ORIGINAL_REPO} ban đầu trống, tài khoản làm việc không có quyền push. Mirror triển khai: {REPO}. Website: {LIVE}. Mô tả Hòa Lạc Food từng thấy trước khi triển khai không là nguồn yêu cầu của ShiloSkin; các ảnh khảo sát cũ chỉ là lịch sử môi trường, không đại diện sản phẩm mới.

## Tính trung thực và hỗ trợ AI
Codex hỗ trợ cả StudentCare và ShiloSkin; không khẳng định kiểm thử mù/độc lập hoàn toàn hoặc chữ ký của sinh viên. Mọi số đo trong báo cáo phải lấy bằng chứng thực thi, phân biệt local/live và chưa chạy/đã chạy. Tài liệu yêu cầu nêu expected behavior, không chứng nhận ứng dụng đang đạt toàn bộ tiêu chí. Bên nhận cần trực tiếp kiểm tra bộ hồ sơ trước khi ký biên bản.

## Tái tạo tài liệu
Chạy `python tools/build_owner_docs.py` từ checkout có module writer tại `../qlychtsv/tools/build_submission.py`, dependencies python-docx/reportlab/openpyxl và font Arial của Windows. Script đặt IDENTITY/PROJECT riêng và truyền đúng thư mục đầu ra; không gọi quy trình xây tài liệu StudentCare. Việc tái tạo không ký thay người dùng và không tạo số đo mới.
"""
    save("README_Nguon_va_tai_lieu_23110306", "NGUỒN VÀ DANH MỤC HỒ SƠ CHỦ HỆ THỐNG", body)


def main():
    urd()
    srs()
    api_doc()
    handover()
    provenance()
    print(f"Generated 5 owner documents × MD/DOCX/PDF in {OUT}; no signatures or test results invented.")


if __name__ == "__main__":
    main()
