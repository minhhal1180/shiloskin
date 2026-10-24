"""Bounded, request-local performance and HTTP-error training defects."""
import re
import time

from flask import g, jsonify, request

EXTRA_BUGS = {
    "P01": "Tìm skin có từ khóa bị chậm hơn 800 ms",
    "P02": "Tải thông báo bị chậm hơn 900 ms",
    "R01": "Skin ID không tồn tại trả 500 thay vì 404",
    "R02": "Giá đăng bán không phải số trả 500 thay vì 400",
}


def install_training_extras(app):
    if app.extensions.get("training_extras"):
        return
    app.extensions["training_extras"] = True

    @app.context_processor
    def training_context():
        return {"training_extras": bool(app.config.get("TRAINING_BUGS"))}

    @app.before_request
    def extra_failures():
        if not app.config.get("TRAINING_BUGS") or not g.get("user"):
            return None
        if request.method == "GET":
            if request.path == "/api/skins" and request.args.get("q", "").strip():
                time.sleep(1.1)
            elif request.path == "/api/notifications":
                time.sleep(1.2)
            else:
                match = re.fullmatch(r"/api/skins/(\d+)", request.path)
                if match and not g.db.execute("SELECT id FROM skins WHERE id=?", (int(match.group(1)),)).fetchone():
                    return jsonify(error="Không thể đọc thông tin skin."), 500
        elif request.method == "POST" and request.path == "/api/listings" and g.user["role"] == "MEMBER":
            data = request.get_json(silent=True)
            if isinstance(data, dict) and isinstance(data.get("price"), str):
                try:
                    int(data["price"])
                except ValueError:
                    return jsonify(error="Không thể chuyển đổi giá đăng bán."), 500
        return None
