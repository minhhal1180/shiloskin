"""ShiloSkin: a fictional-credit CS2 skin inspection and item trading demo."""
import hashlib
import json
import math
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import click
from flask import Flask, abort, g, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from bugs import enabled
from training_extras import install_training_extras

ROLES = ("MEMBER", "MODERATOR", "ADMIN")
RARITIES = ("Consumer Grade", "Industrial Grade", "Mil-Spec", "Restricted", "Classified", "Covert")
WEARS = ("Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def fail(message, status=400):
    abort(status, description=message)


def db():
    if "db" not in g:
        g.db = sqlite3.connect(g.app_db, isolation_level=None, timeout=15)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
        g.db.create_function("casefold", 1, lambda value: str(value).casefold())
    return g.db


def one(sql, args=()):
    row = db().execute(sql, args).fetchone()
    return dict(row) if row else None


def rows(sql, args=()):
    return [dict(row) for row in db().execute(sql, args).fetchall()]


def require(*roles):
    def decorate(fn):
        @wraps(fn)
        def guarded(*args, **kwargs):
            if not g.user:
                fail("Vui lòng đăng nhập.", 401)
            if roles and g.user["role"] not in roles:
                fail("Bạn không có quyền thực hiện thao tác này.", 403)
            return fn(*args, **kwargs)
        return guarded
    return decorate


def data():
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        fail("Dữ liệu gửi lên phải là đối tượng JSON.")
    return value


def text_field(value, name, limit=120, required=True):
    result = value.get(name, "")
    if not isinstance(result, str):
        fail(f"{name} phải là chuỗi.")
    result = result.strip()
    if (required and not result) or len(result) > limit:
        fail(f"{name}: bắt buộc nhập, tối đa {limit} ký tự." if required else f"{name}: tối đa {limit} ký tự.")
    return result


def integer(value, label, minimum=1, maximum=100000):
    try:
        if isinstance(value, bool) or isinstance(value, float) or str(int(value)) != str(value):
            raise ValueError
        result = int(value)
    except (ValueError, TypeError, OverflowError):
        fail(f"{label} phải là số nguyên.")
    if not minimum <= result <= maximum:
        fail(f"{label} phải từ {minimum} đến {maximum}.")
    return result


def item_id(value):
    return integer(value, "ID", maximum=2147483647)


def boolean(value, name, default=True):
    result = value.get(name, default)
    if type(result) is not bool:
        fail(f"{name} phải là true hoặc false.")
    return result


def audit(action, entity_type, entity_id, detail, other_id=None):
    db().execute("INSERT INTO history(actor_id,other_id,action,entity_type,entity_id,detail,created_at) VALUES(?,?,?,?,?,?,?)",
                 (g.user["id"], other_id, action, entity_type, entity_id, detail, now()))


def notify(recipient_id, event, body, entity_type, entity_id):
    db().execute("INSERT INTO notifications(recipient_id,event_type,body,entity_type,entity_id,created_at) VALUES(?,?,?,?,?,?)",
                 (recipient_id, event, body, entity_type, entity_id, now()))


def inventory_item(identifier):
    result = one("SELECT i.*,s.name skin_name,s.weapon,s.rarity,s.wear,s.float_value,s.reference_price,s.active skin_active,u.name owner_name FROM inventory i JOIN skins s ON s.id=i.skin_id JOIN users u ON u.id=i.owner_id WHERE i.id=?", (identifier,))
    if not result:
        fail("Không tìm thấy vật phẩm.", 404)
    result["locked"] = bool(one("SELECT id FROM listings WHERE item_id=? AND status='ACTIVE'", (identifier,)))
    return result


def listing(identifier):
    result = one("SELECT l.*,i.skin_id,s.name skin_name,s.weapon,s.rarity,s.wear,s.float_value,s.reference_price,u.name seller_name FROM listings l JOIN inventory i ON i.id=l.item_id JOIN skins s ON s.id=i.skin_id JOIN users u ON u.id=l.seller_id WHERE l.id=?", (identifier,))
    if not result:
        fail("Không tìm thấy tin đăng.", 404)
    return result


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    secret_path = Path(app.instance_path) / "secret.key"
    if not secret_path.exists():
        secret_path.write_text(secrets.token_hex(32), encoding="utf-8")
    app.config.update(DATABASE=os.getenv("DATABASE", str(Path(app.instance_path) / "shiloskin.db")),
                      SECRET_KEY=os.getenv("SECRET_KEY") or secret_path.read_text(encoding="utf-8"),
                      TRAINING_BUGS=os.getenv("TRAINING_BUGS", "1") == "1",
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                      SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1",
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=8), MAX_CONTENT_LENGTH=1024 * 1024)
    if config:
        app.config.update(config)
    app.config["DUMMY_HASH"] = generate_password_hash(secrets.token_hex(16))

    @app.before_request
    def prepare():
        g.app_db, g.app, g.user = app.config["DATABASE"], app, None
        if not request.path.startswith("/api/"):
            return None
        if request.method in ("POST", "PATCH", "DELETE"):
            db().execute("BEGIN IMMEDIATE")
        if session.get("user_id"):
            user = one("SELECT id,username,name,role,active,balance,session_version FROM users WHERE id=?", (session["user_id"],))
            if user and user["active"] and user["session_version"] == session.get("version"):
                g.user = user
            else:
                session.clear()
        if request.method in ("POST", "PATCH", "DELETE") and request.path != "/api/login":
            if not g.user:
                fail("Phiên hết hạn. Vui lòng đăng nhập.", 401)
            token = request.headers.get("X-CSRF-Token", "")
            if not session.get("csrf") or not secrets.compare_digest(token, session["csrf"]):
                fail("Mã bảo vệ phiên không hợp lệ. Vui lòng tải lại trang.", 403)
            key = request.headers.get("Idempotency-Key")
            if key:
                if len(key) > 100:
                    fail("Idempotency-Key tối đa 100 ký tự.")
                digest = hashlib.sha256(request.get_data(cache=True)).hexdigest()
                g.retry = (g.user["id"], request.method, request.path, key, digest)
                previous = one("SELECT * FROM idempotency WHERE user_id=? AND method=? AND path=? AND request_key=?", g.retry[:4])
                if previous:
                    if previous["digest"] != digest:
                        fail("Khóa retry đã dùng cho nội dung khác.", 409)
                    g.replayed = True
                    return app.response_class(previous["body"], status=previous["status"], mimetype="application/json")
        return None

    @app.after_request
    def finish(response):
        connection = g.get("db")
        if connection and connection.in_transaction:
            if response.status_code < 400:
                if g.get("retry") and not g.get("replayed"):
                    connection.execute("INSERT INTO idempotency(user_id,method,path,request_key,digest,body,status) VALUES(?,?,?,?,?,?,?)",
                                       (*g.retry, response.get_data(as_text=True), response.status_code))
                connection.commit()
            else:
                connection.rollback()
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.teardown_appcontext
    def close(_error):
        connection = g.pop("db", None)
        if connection:
            connection.close()

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.errorhandler(sqlite3.IntegrityError)
    def duplicate_error(_error):
        return jsonify(error="Dữ liệu trùng hoặc tham chiếu không hợp lệ."), 409

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/login")
    def login():
        value = data()
        username = text_field(value, "username", 80)
        password = value.get("password", "")
        if not isinstance(password, str) or not password.strip() or len(password) > 200:
            fail("Vui lòng nhập tài khoản và mật khẩu hợp lệ.")
        user = one("SELECT * FROM users WHERE username=?", (username,))
        valid = check_password_hash(user["password_hash"] if user else app.config["DUMMY_HASH"], password)
        if not user or not valid or not user["active"]:
            fail("Tài khoản hoặc mật khẩu không hợp lệ.", 401)
        session.clear()
        session.permanent = True
        session.update(user_id=user["id"], version=user["session_version"], csrf=secrets.token_hex(24))
        return jsonify(ok=True)

    @app.post("/api/logout")
    @require()
    def logout():
        db().execute("UPDATE users SET session_version=session_version+1 WHERE id=?", (g.user["id"],))
        session.clear()
        return jsonify(ok=True)

    @app.get("/api/me")
    @require()
    def me():
        return jsonify(user={key: g.user[key] for key in ("id", "username", "name", "role", "balance")}, csrf=session["csrf"])

    @app.get("/api/skins")
    @require()
    def skins():
        clauses, args = [], []
        if g.user["role"] != "ADMIN":
            clauses.append("active=1")
        query = request.args.get("q", "").strip()
        if len(query) > 200:
            fail("Từ khóa tối đa 200 ký tự.")
        if query:
            clauses.append("(instr(casefold(name),casefold(?))>0 OR instr(casefold(weapon),casefold(?))>0)")
            args.extend([query, query])
        for field, options in (("rarity", RARITIES), ("wear", WEARS)):
            value = request.args.get(field, "")
            if value:
                if value not in options:
                    fail(f"{field} không hợp lệ.")
                clauses.append(f"{field}=?")
                args.append(value)
        if request.args.get("weapon"):
            clauses.append("weapon=?")
            args.append(request.args["weapon"])
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        return jsonify(items=rows("SELECT * FROM skins" + where + " ORDER BY id", args), rarities=RARITIES, wears=WEARS)

    @app.get("/api/skins/<int:skin_id>")
    @require()
    def skin_detail(skin_id):
        item = one("SELECT * FROM skins WHERE id=?", (skin_id,))
        if not item:
            fail("Không tìm thấy skin.", 404)
        return jsonify(item=item)

    def skin_values(value, old=None):
        value = {**(old or {}), **({"active": bool(old["active"])} if old else {}), **value}
        name, weapon = text_field(value, "name"), text_field(value, "weapon")
        rarity, wear = value.get("rarity"), value.get("wear")
        if rarity not in RARITIES or wear not in WEARS:
            fail("Độ hiếm hoặc tình trạng skin không hợp lệ.")
        try:
            raw_float = value.get("float_value")
            if isinstance(raw_float, bool):
                raise ValueError
            float_value = float(raw_float)
        except (ValueError, TypeError, OverflowError):
            fail("Float phải là số hữu hạn từ 0 đến 1.")
        if not math.isfinite(float_value) or (not enabled(app, "S07") and not 0 <= float_value <= 1):
            fail("Float phải là số hữu hạn từ 0 đến 1.")
        price = integer(value.get("reference_price", 100), "Giá tham khảo")
        active = boolean(value, "active", bool(old["active"]) if old else True)
        return name, weapon, rarity, wear, float_value, price, active

    @app.post("/api/skins")
    @require("ADMIN")
    def create_skin():
        values = skin_values(data())
        stamp = now()
        cursor = db().execute("INSERT INTO skins(name,weapon,rarity,wear,float_value,reference_price,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)", (*values, stamp, stamp))
        audit("CREATE_SKIN", "skin", cursor.lastrowid, values[0])
        return jsonify(id=cursor.lastrowid), 201

    @app.patch("/api/skins/<int:skin_id>")
    @require("ADMIN")
    def edit_skin(skin_id):
        old = one("SELECT * FROM skins WHERE id=?", (skin_id,))
        if not old:
            fail("Không tìm thấy skin.", 404)
        values = skin_values(data(), old)
        db().execute("UPDATE skins SET name=?,weapon=?,rarity=?,wear=?,float_value=?,reference_price=?,active=?,updated_at=? WHERE id=?", (*values, now(), skin_id))
        audit("UPDATE_SKIN", "skin", skin_id, values[0])
        return jsonify(ok=True)

    @app.get("/api/inventory")
    @require()
    def inventory():
        owner_id = item_id(request.args["user_id"]) if request.args.get("user_id") else g.user["id"]
        owner = one("SELECT id,name,username FROM users WHERE id=? AND role='MEMBER'", (owner_id,))
        if not owner and g.user["role"] == "MEMBER":
            fail("Không tìm thấy thành viên.", 404)
        items = rows("SELECT i.*,i.id item_id,s.name skin_name,s.weapon,s.rarity,s.wear,s.float_value,s.reference_price,u.name owner_name,EXISTS(SELECT 1 FROM listings l WHERE l.item_id=i.id AND l.status='ACTIVE') locked FROM inventory i JOIN skins s ON s.id=i.skin_id JOIN users u ON u.id=i.owner_id WHERE i.owner_id=? ORDER BY i.id", (owner_id,))
        for item in items:
            item["locked"] = bool(item["locked"])
        return jsonify(items=items, owner=owner, users=rows("SELECT id,name,username FROM users WHERE role='MEMBER' AND active=1 ORDER BY id"))

    @app.get("/api/listings")
    @require()
    def listings():
        clauses, args = [], []
        if request.args.get("mine") == "1":
            clauses.append("l.seller_id=?")
            args.append(g.user["id"])
        status = request.args.get("status", "")
        if status:
            if status not in ("ACTIVE", "SOLD", "CANCELLED", "HIDDEN"):
                fail("Trạng thái tin đăng không hợp lệ.")
            clauses.append("l.status=?")
            args.append(status)
        query = request.args.get("q", "").strip()
        if len(query) > 200:
            fail("Từ khóa tối đa 200 ký tự.")
        if query:
            clauses.append("(instr(casefold(s.name),casefold(?))>0 OR instr(casefold(s.weapon),casefold(?))>0)")
            args.extend([query, query])
        sql = "SELECT l.*,i.skin_id,s.name skin_name,s.weapon,s.rarity,s.wear,s.float_value,s.reference_price,u.name seller_name,b.name buyer_name FROM listings l JOIN inventory i ON i.id=l.item_id JOIN skins s ON s.id=i.skin_id JOIN users u ON u.id=l.seller_id LEFT JOIN users b ON b.id=l.buyer_id"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        return jsonify(items=rows(sql + " ORDER BY l.id DESC", args))

    @app.post("/api/listings")
    @require("MEMBER")
    def create_listing():
        value = data()
        identifier = item_id(value.get("item_id"))
        item = inventory_item(identifier)
        if item["owner_id"] != g.user["id"]:
            fail("Bạn chỉ được đăng bán vật phẩm của mình.", 403)
        if item["locked"]:
            fail("Vật phẩm đã có tin đăng đang hoạt động.", 409)
        if not item["skin_active"]:
            fail("Skin đã ngừng hoạt động.", 409)
        minimum = 0 if enabled(app, "S01") else 1
        maximum = 1000000000 if enabled(app, "S02") else 100000
        price = integer(value.get("price"), "Giá đăng bán", minimum, maximum)
        stamp = now()
        cursor = db().execute("INSERT INTO listings(item_id,seller_id,price,status,created_at,updated_at) VALUES(?,?,?,'ACTIVE',?,?)", (identifier, g.user["id"], price, stamp, stamp))
        audit("CREATE_LISTING", "listing", cursor.lastrowid, f"{item['skin_name']} · {price} xu")
        notify(g.user["id"], "LISTING_CREATED", f"Đã đăng bán {item['skin_name']}.", "listing", cursor.lastrowid)
        return jsonify(id=cursor.lastrowid), 201

    @app.post("/api/listings/<int:listing_id>/cancel")
    @require("MEMBER")
    def cancel_listing(listing_id):
        item = listing(listing_id)
        if item["seller_id"] != g.user["id"]:
            fail("Chỉ người bán được hủy tin của mình.", 403)
        allowed = ("ACTIVE", "SOLD") if enabled(app, "S05") else ("ACTIVE",)
        if item["status"] not in allowed:
            fail("Chỉ hủy được tin đang hoạt động.", 409)
        db().execute("UPDATE listings SET status='CANCELLED',updated_at=? WHERE id=?", (now(), listing_id))
        audit("CANCEL_LISTING", "listing", listing_id, item["skin_name"])
        return jsonify(ok=True)

    @app.post("/api/listings/<int:listing_id>/buy")
    @require("MEMBER")
    def buy_listing(listing_id):
        item = listing(listing_id)
        if item["status"] != "ACTIVE":
            fail("Tin không còn sẵn để mua.", 409)
        if item["seller_id"] == g.user["id"] and not enabled(app, "S03"):
            fail("Không được tự mua tin của mình.", 409)
        if g.user["balance"] < item["price"] and not enabled(app, "S04"):
            fail("Bạn không đủ xu mô phỏng.", 409)
        current_item = inventory_item(item["item_id"])
        seller = one("SELECT id,active,role FROM users WHERE id=?", (item["seller_id"],))
        if current_item["owner_id"] != item["seller_id"] or not seller["active"] or seller["role"] != "MEMBER":
            fail("Chủ sở hữu tin đăng không còn hợp lệ.", 409)
        stamp = now()
        db().execute("UPDATE users SET balance=balance-? WHERE id=?", (item["price"], g.user["id"]))
        db().execute("UPDATE users SET balance=balance+? WHERE id=?", (item["price"], item["seller_id"]))
        db().execute("UPDATE inventory SET owner_id=?,acquired_at=? WHERE id=?", (g.user["id"], stamp, item["item_id"]))
        db().execute("UPDATE listings SET status='SOLD',buyer_id=?,updated_at=? WHERE id=?", (g.user["id"], stamp, listing_id))
        if not enabled(app, "S10"):
            audit("BUY", "listing", listing_id, f"{item['skin_name']} · {item['price']} xu", item["seller_id"])
        notify(g.user["id"], "BUY", f"Đã mua {item['skin_name']} với {item['price']} xu mô phỏng.", "listing", listing_id)
        if item["seller_id"] != g.user["id"]:
            notify(item["seller_id"], "SOLD", f"{item['skin_name']} đã bán thành công.", "listing", listing_id)
        return jsonify(ok=True, balance=one("SELECT balance FROM users WHERE id=?", (g.user["id"],))["balance"])

    @app.post("/api/listings/<int:listing_id>/moderate")
    @require("MODERATOR")
    def moderate_listing(listing_id):
        item = listing(listing_id)
        if item["status"] != "ACTIVE":
            fail("Chỉ ẩn được tin đang hoạt động.", 409)
        reason = text_field(data(), "reason", 1000, required=not enabled(app, "S08"))
        db().execute("UPDATE listings SET status='HIDDEN',moderation_reason=?,updated_at=? WHERE id=?", (reason, now(), listing_id))
        audit("MODERATE", "listing", listing_id, reason, item["seller_id"])
        notify(item["seller_id"], "MODERATED", f"Tin {item['skin_name']} bị ẩn: {reason}", "listing", listing_id)
        return jsonify(ok=True)

    @app.get("/api/trades")
    @require("MEMBER")
    def trades():
        sql = "SELECT t.*,p.name proposer_name,r.name recipient_name,gs.name give_skin_name,ws.name want_skin_name FROM trades t JOIN users p ON p.id=t.proposer_id JOIN users r ON r.id=t.recipient_id JOIN inventory gi ON gi.id=t.give_item_id JOIN inventory wi ON wi.id=t.want_item_id JOIN skins gs ON gs.id=gi.skin_id JOIN skins ws ON ws.id=wi.skin_id WHERE t.proposer_id=? OR t.recipient_id=? ORDER BY t.id DESC"
        return jsonify(items=rows(sql, (g.user["id"], g.user["id"])))

    @app.post("/api/trades")
    @require("MEMBER")
    def create_trade():
        value = data()
        give_id, want_id = item_id(value.get("give_item_id")), item_id(value.get("want_item_id"))
        give, want = inventory_item(give_id), inventory_item(want_id)
        if give["owner_id"] != g.user["id"]:
            fail("Vật phẩm đề nghị đổi phải thuộc sở hữu của bạn.", 403)
        if give_id == want_id or want["owner_id"] == g.user["id"]:
            fail("Phải chọn vật phẩm của thành viên khác.")
        recipient = one("SELECT id,role,active FROM users WHERE id=?", (want["owner_id"],))
        if not recipient["active"] or recipient["role"] != "MEMBER":
            fail("Người nhận không còn đủ điều kiện giao dịch.", 409)
        if give["locked"] or want["locked"] or not give["skin_active"] or not want["skin_active"]:
            fail("Vật phẩm đang đăng bán hoặc đã ngừng hoạt động.", 409)
        if one("SELECT id FROM trades WHERE give_item_id=? AND want_item_id=? AND status='PENDING'", (give_id, want_id)):
            fail("Đề nghị đổi tương tự đang chờ xử lý.", 409)
        stamp = now()
        cursor = db().execute("INSERT INTO trades(proposer_id,recipient_id,give_item_id,want_item_id,status,created_at,updated_at) VALUES(?,?,?,?,'PENDING',?,?)", (g.user["id"], want["owner_id"], give_id, want_id, stamp, stamp))
        audit("CREATE_TRADE", "trade", cursor.lastrowid, f"{give['skin_name']} ↔ {want['skin_name']}", want["owner_id"])
        notify(want["owner_id"], "TRADE_REQUEST", f"{g.user['name']} đề nghị đổi {give['skin_name']} lấy {want['skin_name']}.", "trade", cursor.lastrowid)
        return jsonify(id=cursor.lastrowid), 201

    @app.post("/api/trades/<int:trade_id>/action")
    @require("MEMBER")
    def trade_action(trade_id):
        item = one("SELECT * FROM trades WHERE id=?", (trade_id,))
        if not item:
            fail("Không tìm thấy đề nghị đổi.", 404)
        action_name = data().get("action")
        if action_name not in ("accept", "reject", "cancel"):
            fail("Thao tác đổi vật phẩm không hợp lệ.")
        allowed_actor = item["proposer_id"] if action_name == "cancel" else item["recipient_id"]
        if allowed_actor != g.user["id"]:
            fail("Bạn không có quyền xử lý đề nghị này.", 403)
        allowed_status = ("PENDING", "REJECTED") if action_name == "accept" and enabled(app, "S06") else ("PENDING",)
        if item["status"] not in allowed_status:
            fail("Đề nghị đã được xử lý hoặc đã kết thúc.", 409)
        if action_name == "accept":
            give, want = inventory_item(item["give_item_id"]), inventory_item(item["want_item_id"])
            proposer = one("SELECT id,active,role FROM users WHERE id=?", (item["proposer_id"],))
            if give["owner_id"] != item["proposer_id"] or want["owner_id"] != item["recipient_id"]:
                fail("Chủ sở hữu vật phẩm đã thay đổi.", 409)
            if give["locked"] or want["locked"] or not give["skin_active"] or not want["skin_active"] or not proposer["active"] or proposer["role"] != "MEMBER":
                fail("Vật phẩm hoặc người gửi không còn đủ điều kiện đổi.", 409)
            stamp = now()
            db().execute("UPDATE inventory SET owner_id=?,acquired_at=? WHERE id=?", (item["recipient_id"], stamp, item["give_item_id"]))
            db().execute("UPDATE inventory SET owner_id=?,acquired_at=? WHERE id=?", (item["proposer_id"], stamp, item["want_item_id"]))
        status = {"accept": "ACCEPTED", "reject": "REJECTED", "cancel": "CANCELLED"}[action_name]
        db().execute("UPDATE trades SET status=?,updated_at=? WHERE id=?", (status, now(), trade_id))
        other = item["proposer_id"] if g.user["id"] == item["recipient_id"] else item["recipient_id"]
        audit("TRADE_" + status, "trade", trade_id, status, other)
        notify(other, "TRADE_" + status, f"Đề nghị đổi #{trade_id}: {status}.", "trade", trade_id)
        return jsonify(ok=True, status=status)

    @app.get("/api/history")
    @require()
    def history():
        return jsonify(items=rows("SELECT h.*,u.name actor_name FROM history h JOIN users u ON u.id=h.actor_id WHERE actor_id=? OR other_id=? ORDER BY h.id DESC", (g.user["id"], g.user["id"])))

    @app.get("/api/notifications")
    @require()
    def notifications():
        return jsonify(items=rows("SELECT * FROM notifications WHERE recipient_id=? ORDER BY id DESC", (g.user["id"],)))

    @app.post("/api/notifications/<int:notification_id>/read")
    @require()
    def read_notification(notification_id):
        if not one("SELECT id FROM notifications WHERE id=? AND recipient_id=?", (notification_id, g.user["id"])):
            fail("Không tìm thấy thông báo.", 404)
        if not enabled(app, "S09"):
            db().execute("UPDATE notifications SET is_read=1 WHERE id=?", (notification_id,))
        return jsonify(ok=True)

    @app.get("/api/users")
    @require("ADMIN")
    def users():
        return jsonify(items=rows("SELECT id,username,name,role,active,balance FROM users ORDER BY id"))

    @app.patch("/api/users/<int:user_id>")
    @require("ADMIN")
    def edit_user(user_id):
        old = one("SELECT * FROM users WHERE id=?", (user_id,))
        if not old:
            fail("Không tìm thấy tài khoản.", 404)
        value = data()
        role = value.get("role", old["role"])
        active = boolean(value, "active", bool(old["active"]))
        if role not in ROLES:
            fail("Vai trò không hợp lệ.")
        name = text_field({**old, **value}, "name")
        if user_id == g.user["id"] and (role != "ADMIN" or not active):
            fail("Không được tự khóa hoặc tự bỏ quyền quản trị.")
        if role != old["role"] and old["role"] == "MEMBER":
            if one("SELECT id FROM listings WHERE seller_id=? AND status='ACTIVE'", (user_id,)) or one("SELECT id FROM trades WHERE (proposer_id=? OR recipient_id=?) AND status='PENDING'", (user_id, user_id)):
                fail("Cần hoàn tất các tin và đề nghị đang hoạt động trước khi đổi vai trò.", 409)
        db().execute("UPDATE users SET name=?,role=?,active=?,session_version=session_version+1 WHERE id=?", (name, role, active, user_id))
        audit("UPDATE_USER", "user", user_id, f"{old['username']} · {role} · {'active' if active else 'locked'}")
        return jsonify(ok=True)

    @app.cli.command("init-db")
    @click.option("--demo", is_flag=True)
    def init_command(demo):
        initialize(app, demo=demo)
        click.echo("Đã khởi tạo SQLite cho ShiloSkin.")

    install_training_extras(app)
    return app


def initialize(app, demo=False):
    with app.app_context():
        g.app_db = app.config["DATABASE"]
        db().execute("PRAGMA journal_mode=WAL")
        db().executescript((Path(__file__).parent / "schema.sql").read_text(encoding="utf-8"))
        if demo and not one("SELECT id FROM users LIMIT 1"):
            db().execute("BEGIN IMMEDIATE")
            password_hash = generate_password_hash("Demo@123")
            for username, name, role, balance in [("member01", "Minh Anh", "MEMBER", 1000), ("member02", "Quốc Bảo", "MEMBER", 1500),
                                                   ("moderator01", "Kiểm duyệt viên", "MODERATOR", 0), ("admin", "Quản trị viên", "ADMIN", 0)]:
                db().execute("INSERT INTO users(username,name,password_hash,role,balance) VALUES(?,?,?,?,?)", (username, name, password_hash, role, balance))
            catalog = [
                ("Redline", "AK-47", "Classified", "Field-Tested", .18, 500),
                ("Printstream", "M4A1-S", "Covert", "Minimal Wear", .09, 1800),
                ("Asiimov", "AWP", "Covert", "Field-Tested", .22, 1400),
                ("Cortex", "USP-S", "Classified", "Factory New", .04, 300),
                ("Water Elemental", "Glock-18", "Classified", "Minimal Wear", .11, 450),
                ("Printstream", "Desert Eagle", "Covert", "Factory New", .03, 2300),
                ("Neo-Noir", "M4A4", "Covert", "Field-Tested", .17, 900),
                ("Asiimov", "P250", "Classified", "Well-Worn", .40, 250),
                ("Mecha Industries", "FAMAS", "Classified", "Minimal Wear", .10, 380),
                ("Eco", "Galil AR", "Classified", "Battle-Scarred", .68, 320),
                ("Mount Fuji", "MP9", "Restricted", "Factory New", .05, 200),
                ("Abyss", "SSG 08", "Mil-Spec", "Field-Tested", .26, 120),
            ]
            stamp = now()
            for name, weapon, rarity, wear, float_value, reference_price in catalog:
                db().execute("INSERT INTO skins(name,weapon,rarity,wear,float_value,reference_price,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)", (name, weapon, rarity, wear, float_value, reference_price, stamp, stamp))
            for skin_id in range(1, 9):
                db().execute("INSERT INTO inventory(skin_id,owner_id,acquired_at) VALUES(?,?,?)", (skin_id, 1 if skin_id <= 4 else 2, stamp))
            for identifier, price in [(5, 400), (6, 2200)]:
                db().execute("INSERT INTO listings(item_id,seller_id,price,status,created_at,updated_at) VALUES(?,2,?,'ACTIVE',?,?)", (identifier, price, stamp, stamp))
            for recipient_id in (1, 2):
                db().execute("INSERT INTO notifications(recipient_id,event_type,body,entity_type,entity_id,created_at) VALUES(?,'WELCOME','Chào mừng đến ShiloSkin. Mọi số dư đều là xu mô phỏng.','user',?,?)", (recipient_id, recipient_id, stamp))
            db().commit()


if __name__ == "__main__":
    application = create_app()
    if not Path(application.config["DATABASE"]).exists():
        initialize(application, demo=True)
    application.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5001")), debug=False)
