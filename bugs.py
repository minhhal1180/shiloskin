"""Private teaching switches: ten deliberately incorrect business rules."""

BUGS = {
    "S01": "Cho phép đăng bán với giá 0 xu",
    "S02": "Cho phép giá đăng bán vượt 100000 xu",
    "S03": "Cho phép người bán tự mua tin của mình",
    "S04": "Cho phép mua khi không đủ xu mô phỏng",
    "S05": "Cho phép hủy tin đã bán thành công",
    "S06": "Cho phép chấp nhận đề nghị đã bị từ chối",
    "S07": "Cho phép admin lưu float nằm ngoài [0,1]",
    "S08": "Cho phép kiểm duyệt ẩn tin mà không có lý do",
    "S09": "Đánh dấu thông báo đã đọc nhưng không lưu",
    "S10": "Mua thành công không ghi lịch sử giao dịch",
}


def enabled(app, bug_id):
    return bool(app.config.get("TRAINING_BUGS")) and bug_id in BUGS
