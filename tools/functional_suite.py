"""Executable CS2 training-market functional dossier, with isolated test data.

No real Steam inventory or real-money trading is involved. This is informed,
AI-assisted testing of the paired training project, not a blind independent test.
Run after backend setup: python tools/functional_suite.py --mode both
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
import time
import traceback
from collections import Counter
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
SUB=ROOT.parent/"qlychtsv"/"submission"/"partner"
sys.path.insert(0,str(ROOT))
CASES=[]
COUNTERS=Counter()
SCOPE="Kiểm thử hệ thống ShiloSkin của bạn cặp được AI hỗ trợ dựng; có biết mã nguồn và lỗi cài sẵn, không phải kiểm thử mù độc lập."
RESPONSIBLE_TESTER="Bùi Xuân Minh – 23110193"
SYSTEM_OWNER="Nguyễn Từ Lân – 23110306"
EXECUTION_OPERATOR="Codex automation theo yêu cầu người dùng; cả hai hệ thống được AI hỗ trợ, không phải kiểm thử mù hoặc chạy tay của sinh viên."
TECHNIQUES={"Positive":"Phân hoạch tương đương (EP)","Negative":"Phân hoạch tương đương (EP)",
            "Boundary":"Giá trị biên (BVA)","Permission":"Bảng quyết định","State":"Chuyển trạng thái",
            "E2E":"Use case / E2E"}


def register(fr,title,expected,*,kind="Positive",bug="",data=None,steps=None,case_id=None,requirements=None):
    def wrap(fn):
        COUNTERS[fr]+=1
        CASES.append({"id":case_id or f"TC-{fr.replace('-','')}-{COUNTERS[fr]:03d}","function_id":fr,
                      "title":title,"preconditions":"SQLite mới với dữ liệu mẫu; member01=1000coins, member02=1500coins; loại tiền hoàn toàn ảo.",
                      "data":data or {},"steps":steps or ["Đăng nhập vai trò nêu trong testcase.","Gửi request theo dữ liệu và tiền điều kiện.","Đối chiếu HTTP, trạng thái và dữ liệu hậu điều kiện."],
                      "expected":expected,"bug_id":bug,"test_kind":kind,"technique":TECHNIQUES[kind],"requirements":requirements or [fr],"fn":fn})
        return fn
    return wrap


class Check:
    def __init__(self,app):
        self.app=app
        self.clients={}
        self.trace=[]

    def eq(self,actual,expected,label="Đối chiếu"):
        self.trace.append({"assertion":label,"actual":actual,"expected":expected,"passed":actual==expected})
        if actual!=expected:raise AssertionError(f"{label}: expected={expected!r}, actual={actual!r}")

    def truth(self,value,label="Điều kiện phải đúng"):self.eq(bool(value),True,label)

    def capture(self,method,path,actor,data,response):
        body=response.get_json(silent=True)
        if body is None:body={"bytes":len(response.data),"preview":response.data[:160].decode("utf-8",errors="replace")}
        if isinstance(body,dict) and "csrf" in body:body={**body,"csrf":"[redacted]"}
        if isinstance(data,dict):data={k:"[redacted]" if k=="password" else v for k,v in data.items()}
        self.trace.append({"method":method,"path":"/api"+path,"actor":actor or "anonymous","input":data,"http_status":response.status_code,"response":body})
        return response

    def client(self,actor):
        if actor not in self.clients:
            client=self.app.test_client()
            body={"username":actor,"password":"Demo@123"}
            response=client.post("/api/login",json=body)
            self.capture("POST","/login",actor,body,response)
            self.eq(response.status_code,200,"Đăng nhập tiền điều kiện")
            response=client.get("/api/me")
            self.capture("GET","/me",actor,None,response)
            self.eq(response.status_code,200,"Lấy thông tin phiên tiền điều kiện")
            self.clients[actor]=(client,response.json["csrf"])
        return self.clients[actor]

    def request(self,actor,method,path,data=None,headers=None):
        client,token=self.client(actor) if actor else (self.app.test_client(),"")
        options={"method":method,"headers":{"X-CSRF-Token":token,**(headers or {})}}
        if method!="GET":options["json"]=data or {}
        response=client.open("/api"+path,**options)
        return self.capture(method,path,actor,data,response)

    def get(self,actor,path):return self.request(actor,"GET",path)
    def post(self,actor,path,data=None,**options):return self.request(actor,"POST",path,data,**options)
    def patch(self,actor,path,data):return self.request(actor,"PATCH",path,data)

    def items(self,actor,path):
        response=self.get(actor,path);self.eq(response.status_code,200,"Đọc danh sách tiền điều kiện");return response.json["items"]

    def login(self,username,password):
        client=self.app.test_client();data={"username":username,"password":password}
        response=client.post("/api/login",json=data)
        return self.capture("POST","/login",None,data,response)

    def listing(self,item=1,price=200,actor="member01"):
        response=self.post(actor,"/listings",{"item_id":item,"price":price})
        self.eq(response.status_code,201,"Tạo listing tiền điều kiện")
        return response.json["id"]

    def trade(self,give=1,want=7,actor="member01"):
        response=self.post(actor,"/trades",{"give_item_id":give,"want_item_id":want})
        self.eq(response.status_code,201,"Tạo trade tiền điều kiện")
        return response.json["id"]

    def act(self,trade,action,actor="member02"):return self.post(actor,f"/trades/{trade}/action",{"action":action})
    def balance(self,actor):
        response=self.get(actor,"/me");self.eq(response.status_code,200);return response.json["user"]["balance"]

    def listing_item(self,listing,actor="member01"):
        # The published contract exposes full listing rows through the list API.
        items=self.items(actor,"/listings")
        matches=[item for item in items if item["id"]==listing]
        self.eq(len(matches),1,"Listing vừa tạo/giao dịch vẫn có bản ghi lịch sử trạng thái")
        return matches[0]


# FR-01 authentication/session.
for actor,role in [("member01","MEMBER"),("moderator01","MODERATOR"),("admin","ADMIN")]:
    @register("FR-01",f"Đăng nhập hợp lệ {actor}",f"HTTP200, user.role={role}.",data={"username":actor,"password":"Demo@123 (tài khoản mẫu)"})
    def valid_login(c,actor=actor,role=role):
        response=c.get(actor,"/me");c.eq(response.status_code,200);c.eq(response.json["user"]["role"],role)

for username,password,status,title in [("member01","wrong",401,"Sai mật khẩu"),("unknown","wrong",401,"Tài khoản không tồn tại"),("","Demo@123",400,"Tên tài khoản rỗng"),("member01","",400,"Mật khẩu rỗng")]:
    @register("FR-01",title,f"HTTP{status}; không tạo phiên.",kind="Negative")
    def bad_login(c,username=username,password=password,status=status):c.eq(c.login(username,password).status_code,status)

@register("FR-01","Đăng xuất thu hồi cookie cũ","Logout200; dùng lại cookie cũ GET/me trả401.",kind="State")
def logout(c):
    client,_=c.client("member01");cookie=client.get_cookie("session").value
    c.eq(c.post("member01","/logout").status_code,200);client.set_cookie("session",cookie)
    response=client.get("/api/me");c.capture("GET","/me","member01",None,response);c.eq(response.status_code,401)

@register("FR-01","API riêng tư từ chối người ẩn danh","GET/inventory trả401.",kind="Permission")
def anonymous(c):c.eq(c.get(None,"/inventory").status_code,401)

# FR-02 catalogue/search.
@register("FR-02","Danh mục có12model dữ liệu mẫu","GET/skins200; có12skin, mỗi skin có id/name/weapon/float_value.")
def catalogue(c):
    items=c.items("member01","/skins");c.eq(len(items),12)
    for item in items:c.truth(all(key in item for key in ["id","name","weapon","float_value"]))

@register("FR-02","Tìm skin theo chuỗi tên","Tìm chuỗi con của tên model1 trả chứa id1.")
def skin_search(c):
    first=c.items("member01","/skins")[0]
    query=first["name"].split()[0]
    items=c.items("member01","/skins?"+urlencode({"q":query}));c.truth(first["id"] in [i["id"] for i in items])

@register("FR-02","Tìm không có kết quả","Từ khóa không khớp trả items rỗng, HTTP200.",kind="Negative")
def skin_search_empty(c):c.eq(c.items("member01","/skins?q=NO_MATCH_QXZ_23110193"),[])

@register("FR-02","Tìm không phân biệt hoa thường","Cùng từ khóa upper/lower cho cùng tậpid.")
def search_casefold(c):
    first=c.items("member01","/skins")[0];query=first["name"].split()[0]
    a=c.items("member01","/skins?"+urlencode({"q":query.upper()}));b=c.items("member01","/skins?"+urlencode({"q":query.lower()}))
    c.eq([i["id"] for i in a],[i["id"] for i in b])

# FR-03 detail/check.
@register("FR-03","Kiểm tra chi tiết model tồn tại","GET/skins/1 trả200; id1 và float trong[0,1].")
def detail_skin(c):
    response=c.get("member01","/skins/1");c.eq(response.status_code,200)
    item=response.json.get("item",response.json);c.eq(item["id"],1);c.truth(0<=item["float_value"]<=1)

@register("FR-03","Chi tiết skin ID không tồn tại","GET/skins/999999 phải404, không500.",kind="Negative",bug="R01")
def missing_skin(c):c.eq(c.get("member01","/skins/999999").status_code,404)

@register("FR-03","Chi tiết giữ nguyên reference_price của catalog","Model1 detail có reference_price bằng listingmodel của catalog.")
def detail_matches(c):
    source=next(i for i in c.items("member01","/skins") if i["id"]==1)
    detail=c.get("member01","/skins/1");c.eq(detail.status_code,200);item=detail.json.get("item",detail.json)
    c.eq(item["reference_price"],source["reference_price"]);c.eq(item["wear"],source["wear"])

# FR-04 inventory.
@register("FR-04","Mặc định member01 xem kho của mình","Inventory chứa items1..4, owner_id1.")
def inventory_own(c):
    items=c.items("member01","/inventory");c.eq([i["id"] for i in items],[1,2,3,4]);c.truth(all(i["owner_id"]==1 for i in items))

@register("FR-04","Xem metadata kho public của người nhận trade","member01 GET/inventory?user_id=2 thấy items5..8, owner_id2.")
def inventory_other(c):
    items=c.items("member01","/inventory?user_id=2");c.eq([i["id"] for i in items],[5,6,7,8]);c.truth(all(i["owner_id"]==2 for i in items))

@register("FR-04","Item đang rao bị khóa cho giao dịch","Items5/6 trong kho member02 có locked=true; item7khôngkhóa.")
def inventory_locked(c):
    items={i["id"]:i for i in c.items("member02","/inventory")};c.truth(items[5]["locked"]);c.truth(items[6]["locked"]);c.eq(bool(items[7]["locked"]),False)

# FR-05 listing validation.
@register("FR-05","Tạo listing hợp lệ với item sở hữu","POST item1 price200 trả201; listing ACTIVE seller_id1.")
def listing_valid(c):
    listing=c.listing();item=c.listing_item(listing);c.eq(item["status"],"ACTIVE");c.eq(item["seller_id"],1);c.eq(item["price"],200)

for price,title,bug in [(0,"Giá0 phải bị chặn","S01"),(100001,"Giá vượt100000 phải bị chặn","S02"),(-1,"Giá âm phải bị chặn",""),("abc","Giá không phải số không được gây500","R02")]:
    @register("FR-05",title,"POST/listings trả400, không tạo listing.",kind="Boundary" if isinstance(price,int) else "Negative",bug=bug,data={"item_id":1,"price":price})
    def bad_price(c,price=price):c.eq(c.post("member01","/listings",{"item_id":1,"price":price}).status_code,400)

@register("FR-05","Không rao item thuộc người khác","member01 rao item7 của member02 trả403.",kind="Permission")
def listing_other(c):c.eq(c.post("member01","/listings",{"item_id":7,"price":100}).status_code,403)

@register("FR-05","Không rao lại item đang ACTIVE","Rao item1hai lần, lần2trả409.",kind="State")
def duplicate_listing(c):
    c.listing();c.eq(c.post("member01","/listings",{"item_id":1,"price":200}).status_code,409)

@register("FR-05","Giá biên1 và100000 đều hợp lệ","Tạo item1price1 vàitem2price100000 đều201.",kind="Boundary")
def valid_price_boundaries(c):
    c.eq(c.post("member01","/listings",{"item_id":1,"price":1}).status_code,201)
    c.eq(c.post("member01","/listings",{"item_id":2,"price":100000}).status_code,201)

# FR-06 cancellation.
@register("FR-06","Chủ listing hủy ACTIVE","Cancel200; statusCANCELLED; item mở khóa.")
def cancel_active(c):
    listing=c.listing();c.eq(c.post("member01",f"/listings/{listing}/cancel").status_code,200)
    c.eq(c.listing_item(listing)["status"],"CANCELLED");item=next(i for i in c.items("member01","/inventory") if i["id"]==1);c.eq(bool(item["locked"]),False)

@register("FR-06","Người khác không hủy listing","member01 hủy listing1củamember02 trả403.",kind="Permission")
def cancel_other(c):c.eq(c.post("member01","/listings/1/cancel").status_code,403)

@register("FR-06","Không hủy listing đã bán","member01 mua listing1; member02 cancel phải409, giữSOLD.",kind="State",bug="S05")
def cancel_sold(c):
    c.eq(c.post("member01","/listings/1/buy").status_code,200)
    c.eq(c.post("member02","/listings/1/cancel").status_code,409);c.eq(c.listing_item(1)["status"],"SOLD")

@register("FR-06","Hủy lần hai bị từ chối","CancelCANCELLED trả409.",kind="State")
def cancel_twice(c):
    listing=c.listing();c.eq(c.post("member01",f"/listings/{listing}/cancel").status_code,200);c.eq(c.post("member01",f"/listings/{listing}/cancel").status_code,409)

# FR-07 buying.
@register("FR-07","Mua listing của người khác đủcoins","Buylisting1trả200;SOLD; item5chuyểnsangmember01; balance600/1900.")
def buy_valid(c):
    c.eq(c.post("member01","/listings/1/buy").status_code,200)
    c.eq(c.listing_item(1)["status"],"SOLD");c.eq(c.balance("member01"),600);c.eq(c.balance("member02"),1900)
    c.truth(5 in [i["id"] for i in c.items("member01","/inventory")])

@register("FR-07","Không tự mua listing của mình","member01 tựmuaitem1đangrao trả409; không đổi coins.",kind="Permission",bug="S03")
def self_buy(c):
    listing=c.listing();c.eq(c.post("member01",f"/listings/{listing}/buy").status_code,409);c.eq(c.balance("member01"),1000)

@register("FR-07","Không mua khi thiếucoins","member01balance1000mualisting2price2200 trả409; balancekhôngâm.",kind="Boundary",bug="S04")
def insufficient(c):c.eq(c.post("member01","/listings/2/buy").status_code,409);c.eq(c.balance("member01"),1000)

@register("FR-07","Không mua listing đã bán lần hai","Buylần2trả409; sốdưkhôngbịtrừlần2.",kind="State")
def buy_twice(c):
    c.eq(c.post("member01","/listings/1/buy").status_code,200);c.eq(c.post("member01","/listings/1/buy").status_code,409);c.eq(c.balance("member01"),600)

@register("FR-07","Không mua listing đã hủy","Sellerhủylisting1; member01buyphải409.",kind="State")
def buy_cancelled(c):
    c.eq(c.post("member02","/listings/1/cancel").status_code,200);c.eq(c.post("member01","/listings/1/buy").status_code,409)

@register("FR-07","Mua listing ID không tồn tại","POST/listings/99999/buy trả404.",kind="Negative")
def buy_missing(c):c.eq(c.post("member01","/listings/99999/buy").status_code,404)

# FR-08 creating swaps.
@register("FR-08","Tạo đề nghị trao đổi item1lấyitem7","POST201; tradeshownPENDING, đúnggive/wantitem.")
def trade_create(c):
    trade=c.trade();items=c.items("member01","/trades");item=next(i for i in items if i["id"]==trade)
    c.eq(item["status"],"PENDING");c.eq(item["give_item_id"],1);c.eq(item["want_item_id"],7)

@register("FR-08","Không offer item không thuộc mình","member01give7want1trả403.",kind="Permission")
def trade_other_give(c):c.eq(c.post("member01","/trades",{"give_item_id":7,"want_item_id":1}).status_code,403)

@register("FR-08","Không tạo trade với hai item cùng chủ","Give1want2đềucủamember01trả400.",kind="Negative")
def trade_same_owner(c):c.eq(c.post("member01","/trades",{"give_item_id":1,"want_item_id":2}).status_code,400)

@register("FR-08","Không trade item đang ACTIVElisting","Give1want5đangrao trả409.",kind="State")
def trade_listed(c):c.eq(c.post("member01","/trades",{"give_item_id":1,"want_item_id":5}).status_code,409)

@register("FR-08","Chặn trùng cặp item đang PENDING","Tạocùnggive/wantlần2trả409.",kind="State")
def trade_duplicate(c):c.trade();c.eq(c.post("member01","/trades",{"give_item_id":1,"want_item_id":7}).status_code,409)

# FR-09 acceptance.
@register("FR-09","Người nhận chấp nhận PENDING đổi quyền sở hữu","Accept200;item1củamember02,item7củamember01; coinskhôngđổi.")
def accept_trade(c):
    trade=c.trade();c.eq(c.act(trade,"accept").status_code,200)
    c.truth(7 in [i["id"] for i in c.items("member01","/inventory")]);c.truth(1 in [i["id"] for i in c.items("member02","/inventory")])
    c.eq(c.balance("member01"),1000);c.eq(c.balance("member02"),1500)

@register("FR-09","Người gửi không accept offer của mình","member01accepttradeđãgửi trả403.",kind="Permission")
def sender_accept(c):c.eq(c.act(c.trade(),"accept",actor="member01").status_code,403)

@register("FR-09","Không accept offer đã REJECTED","Ngườinhậntừchối,rồiacceptphải409.",kind="State",bug="S06")
def accept_rejected(c):
    trade=c.trade();c.eq(c.act(trade,"reject").status_code,200);c.eq(c.act(trade,"accept").status_code,409)

@register("FR-09","Không accept nếu item đã rao sau khi tạo offer","OfferPENDING; giverraoitềm1;recipientaccept409.",kind="State")
def accept_item_now_listed(c):
    trade=c.trade();c.listing();c.eq(c.act(trade,"accept").status_code,409)

# FR-10 reject/cancel.
@register("FR-10","Người nhận từ chối PENDING","Reject200;REJECTED; haiitemkhôngđổichủ.")
def reject_trade(c):
    trade=c.trade();c.eq(c.act(trade,"reject").status_code,200);item=next(i for i in c.items("member01","/trades") if i["id"]==trade);c.eq(item["status"],"REJECTED")
    c.truth(1 in [i["id"] for i in c.items("member01","/inventory")])

@register("FR-10","Người gửi hủy PENDING","Cancel200;CANCELLED.")
def cancel_trade(c):
    trade=c.trade();c.eq(c.act(trade,"cancel",actor="member01").status_code,200);item=next(i for i in c.items("member01","/trades") if i["id"]==trade);c.eq(item["status"],"CANCELLED")

@register("FR-10","Người nhận không được hủy với vai người gửi","Recipientcanceltrả403.",kind="Permission")
def recipient_cancel(c):c.eq(c.act(c.trade(),"cancel").status_code,403)

@register("FR-10","Không reject hai lần","RejectPENDING200;rồirejectREJECTED409.",kind="State")
def reject_twice(c):
    trade=c.trade();c.eq(c.act(trade,"reject").status_code,200);c.eq(c.act(trade,"reject").status_code,409)

# FR-11 history.
@register("FR-11","Tạo listing lưu event lịch sử","Saucreate,historycóeventliênquanlistingmới.")
def history_create(c):
    listing=c.listing();items=c.items("member01","/history");c.truth(any(str(listing) in str(i) and 'LIST' in str(i.get('action','')).upper() for i in items))

@register("FR-11","Mua listing lưu BUY/SALE audit","BuythànhcôngphảicóBUYhoặcPURCHASEeventtronghistorybuyer.",bug="S10")
def history_buy(c):
    c.eq(c.post("member01","/listings/1/buy").status_code,200);items=c.items("member01","/history")
    c.truth(any(any(word in str(i.get("action","")).upper() for word in ["BUY","PURCHASE","SALE"]) for i in items),"Mua thành công phải có audit BUY")

@register("FR-11","Lịch sử không được đọc khi chưa đăng nhập","GET/historyẩn danh401.",kind="Permission")
def history_anonymous(c):c.eq(c.get(None,"/history").status_code,401)

# FR-12 profile and virtual coins.
@register("FR-12","Hồ sơ trả số dưảo ban đầu đúng","member01balance1000,member02balance1500.")
def profile_balance(c):c.eq(c.balance("member01"),1000);c.eq(c.balance("member02"),1500)

@register("FR-12","Giao dịch mua bảo toàn tổngcoins hai bên","Tổngtrướcvàsau2500; buyer-400,seller+400.")
def conserved_balance(c):
    before=c.balance("member01")+c.balance("member02");c.eq(c.post("member01","/listings/1/buy").status_code,200)
    c.eq(c.balance("member01")+c.balance("member02"),before)

@register("FR-12","Hồ sơ không trảpasswordhash","/mekhôngcópassword/password_hash,trảname/username/role/balance.")
def profile_shape(c):
    user=c.get("member01","/me").json["user"];c.truth(all(k in user for k in ["id","name","username","role","balance"]));c.truth("password" not in user and "password_hash" not in user)

# FR-13 moderation.
@register("FR-13","Moderator ẩn listing có lý do","Moderate200,statusHIDDEN;buybịchặn409.")
def hide_valid(c):
    c.eq(c.post("moderator01","/listings/1/moderate",{"reason":"Mô tả chưa rõ."}).status_code,200)
    c.eq(c.listing_item(1)["status"],"HIDDEN");c.eq(c.post("member01","/listings/1/buy").status_code,409)

@register("FR-13","Ẩn listing bắt buộc lý do","Reasonrỗngtrả400;listingvẫnACTIVE.",kind="Negative",bug="S08")
def hide_empty(c):c.eq(c.post("moderator01","/listings/1/moderate",{"reason":""}).status_code,400)

@register("FR-13","Member không được kiểm duyệt listing","Membermoderate trả403.",kind="Permission")
def member_hide(c):c.eq(c.post("member01","/listings/1/moderate",{"reason":"Nội dung"}).status_code,403)

@register("FR-13","Moderator không ẩn listing đã SOLD","Buysuccess;rồimoderatephải409.",kind="State")
def hide_sold(c):
    c.eq(c.post("member01","/listings/1/buy").status_code,200);c.eq(c.post("moderator01","/listings/1/moderate",{"reason":"Nội dung"}).status_code,409)

# FR-14 users.
@register("FR-14","Admin xem danh sách4tài khoản mẫu","GET/users200;cómember01/member02/moderator01/admin;khônghash.")
def admin_users(c):
    items=c.items("admin","/users");c.eq(len(items),4);c.truth(all("password_hash" not in i for i in items))

@register("FR-14","Member không xem quản trịuser","GET/users403.",kind="Permission")
def member_users(c):c.eq(c.get("member01","/users").status_code,403)

@register("FR-14","Admin khóa tài khoản thu hồi phiên","PATCHactivefalse200;member02/me401.",kind="State")
def admin_lock(c):
    client,_=c.client("member02");c.eq(c.patch("admin","/users/2",{"active":False}).status_code,200)
    response=client.get("/api/me");c.capture("GET","/me","member02",None,response);c.eq(response.status_code,401)

@register("FR-14","Admin không tự khóa mình","PATCH/users/4activefalse400.",kind="Permission")
def admin_self_lock(c):c.eq(c.patch("admin","/users/4",{"active":False}).status_code,400)

@register("FR-14","Đổi role ngoàienum bị chặn","PATCHroleOWNER400.",kind="Negative")
def admin_bad_role(c):c.eq(c.patch("admin","/users/2",{"role":"OWNER"}).status_code,400)

# FR-15 skin catalogue administration.
SKIN={"name":"AK-47 | Test Pattern","weapon":"AK-47","rarity":"Restricted","wear":"Field-Tested","float_value":0.25,"reference_price":250}

@register("FR-15","Admin tạo model skin hợp lệ","POST/skins201;modelmớixuấthiệncatalog.",data=SKIN)
def admin_skin(c):
    response=c.post("admin","/skins",SKIN);c.eq(response.status_code,201);c.truth(response.json["id"] in [i["id"] for i in c.items("member01","/skins")])

@register("FR-15","Float vượt1không hợp lệ","POSTfloat_value1.2trả400.",kind="Boundary",bug="S07",data={**SKIN,"float_value":1.2})
def bad_float(c):c.eq(c.post("admin","/skins",{**SKIN,"float_value":1.2}).status_code,400)

@register("FR-15","Tên skin rỗng bị chặn","POSTnamewhitespace400.",kind="Negative")
def empty_skin_name(c):c.eq(c.post("admin","/skins",{**SKIN,"name":"   "}).status_code,400)

@register("FR-15","Rarity không thuộcenum bị chặn","POSTrarityLegendary400.",kind="Negative")
def bad_rarity(c):c.eq(c.post("admin","/skins",{**SKIN,"rarity":"Legendary"}).status_code,400)

@register("FR-15","Member không tạo model skin","POST/skins403.",kind="Permission")
def member_create_skin(c):c.eq(c.post("member01","/skins",SKIN).status_code,403)

@register("FR-15","Admin sửa reference_price model","PATCH/skins/1reference_price300200;detailgiá300.")
def edit_skin(c):
    c.eq(c.patch("admin","/skins/1",{"reference_price":300}).status_code,200)
    response=c.get("member01","/skins/1");c.eq(response.status_code,200);item=response.json.get("item",response.json);c.eq(item["reference_price"],300)

# FR-16 notifications.
@register("FR-16","Bên nhận trade có thông báo","Tạotrade;member02cónotificationliênquantrade.")
def notify_trade(c):
    c.trade();items=c.items("member02","/notifications");c.truth(len(items)>0)

@register("FR-16","Đánh dấu đã đọc phải được lưu","POSTread200;GETlạinotificationis_read1.",bug="S09")
def notify_read(c):
    c.trade();item=c.items("member02","/notifications")[0]
    c.eq(c.post("member02",f'/notifications/{item["id"]}/read').status_code,200)
    updated=next(i for i in c.items("member02","/notifications") if i["id"]==item["id"]);c.eq(updated["is_read"],1)

@register("FR-16","Không đánh dấu thông báo người khác","member01readnotificationmember02trả404.",kind="Permission")
def notify_other(c):
    c.trade();item=c.items("member02","/notifications")[0];c.eq(c.post("member01",f'/notifications/{item["id"]}/read').status_code,404)

@register("FR-16","ID thông báo không tồn tại","POST/read99999trả404.",kind="Negative")
def notify_missing(c):c.eq(c.post("member01","/notifications/99999/read").status_code,404)


# Nine complete use-case scenarios across the three documented workflows.
@register("FR-07","FLOW01-A: rao bán → người khác mua → nhận coins/item","Seller1+200coins,buyer2-200coins,item1đổichủ,SOLD.",kind="E2E",case_id="TC-FLOW01-001",requirements=["FR-04","FR-05","FR-07","FR-12"],steps=["member01raoitem1giá200.","member02xemdanhmụcvàmua.","KiểmtraSOLD,itemchuyểnsangmember02,balance1200/1300."])
def flow_01a(c):
    listing=c.listing();c.eq(c.post("member02",f"/listings/{listing}/buy").status_code,200)
    c.eq(c.listing_item(listing)["status"],"SOLD");c.eq(c.balance("member01"),1200);c.eq(c.balance("member02"),1300);c.truth(1 in [i["id"] for i in c.items("member02","/inventory")])

@register("FR-06","FLOW01-B: rao bán → hủy → rao lại","ListingđầutiênCANCELLED;itemmởkhóavàraolạiACTIVE.",kind="E2E",case_id="TC-FLOW01-002",requirements=["FR-04","FR-05","FR-06"],steps=["member01raoitem1.","Chínhchủhủylisting.","Rao lạiitem1giá350vàxemACTIVE."])
def flow_01b(c):
    listing=c.listing();c.eq(c.post("member01",f"/listings/{listing}/cancel").status_code,200)
    second=c.listing(price=350);c.eq(c.listing_item(listing)["status"],"CANCELLED");c.eq(c.listing_item(second)["status"],"ACTIVE")

@register("FR-11","FLOW01-C: mua listing mẫu → kiểm tra audit và bảo toàn coins","Buysuccess;historybuyerhassaleevent;tổngcoins2500.",kind="E2E",case_id="TC-FLOW01-003",requirements=["FR-07","FR-11","FR-12"],bug="S10",steps=["member01mualisting1price400.","Đọc/mehaibênvà/historybuyer.","ĐốichiếuauditBUYvàtổngcoins."])
def flow_01c(c):
    c.eq(c.post("member01","/listings/1/buy").status_code,200);c.eq(c.balance("member01")+c.balance("member02"),2500)
    c.truth(any(any(word in str(i.get("action","")).upper() for word in ["BUY","PURCHASE","SALE"]) for i in c.items("member01","/history")),"Mua phải có audit")

@register("FR-09","FLOW02-A: offer → recipientaccept → itemđổichủ","OfferACCEPTED;item1và7đổichủ;coinskhôngđổi.",kind="E2E",case_id="TC-FLOW02-001",requirements=["FR-04","FR-08","FR-09","FR-12","FR-16"],steps=["member01offeritem1lấy7.","member02nhậnthôngbáovàaccept.","KiểmtratradeACCEPTED,khohaibênvàcoins."])
def flow_02a(c):
    trade=c.trade();c.truth(len(c.items("member02","/notifications"))>0);c.eq(c.act(trade,"accept").status_code,200)
    item=next(i for i in c.items("member01","/trades") if i["id"]==trade);c.eq(item["status"],"ACCEPTED")
    c.truth(7 in [i["id"] for i in c.items("member01","/inventory")]);c.truth(1 in [i["id"] for i in c.items("member02","/inventory")]);c.eq(c.balance("member01"),1000)

@register("FR-10","FLOW02-B: offer → recipientreject → thửacceptbịchặn","REJECTEDkhôngđượcaccept;khôngđổichủ.",kind="E2E",case_id="TC-FLOW02-002",requirements=["FR-08","FR-09","FR-10"],bug="S06",steps=["member01tạooffer.","member02reject.","member02thửacceptofferREJECTED;đốichiếu409vàquyềnsởhữu."])
def flow_02b(c):
    trade=c.trade();c.eq(c.act(trade,"reject").status_code,200);c.eq(c.act(trade,"accept").status_code,409);c.truth(1 in [i["id"] for i in c.items("member01","/inventory")])

@register("FR-10","FLOW02-C: offer → sendercancel → recipientacceptbịchặn","CANCELLEDgiữquyềnsởhữu;accept409.",kind="E2E",case_id="TC-FLOW02-003",requirements=["FR-08","FR-09","FR-10"],steps=["member01tạoofferitem1lấy7.","member01hủyoffer.","member02acceptphải409;kiểmtraCANCELLED."])
def flow_02c(c):
    trade=c.trade();c.eq(c.act(trade,"cancel",actor="member01").status_code,200);c.eq(c.act(trade,"accept").status_code,409)
    c.eq(next(i for i in c.items("member01","/trades") if i["id"]==trade)["status"],"CANCELLED")

@register("FR-13","FLOW03-A: rao bán → moderatorẩn → chặn mua","HIDDEN;buyerbuy409;itemvàcoinskhôngđổichủ.",kind="E2E",case_id="TC-FLOW03-001",requirements=["FR-05","FR-07","FR-13"],steps=["member01raoitem1.","moderator01ẩnlistingvớilýdo.","member02thửmua;kiểmtraHIDDENvàcoins."])
def flow_03a(c):
    listing=c.listing();c.eq(c.post("moderator01",f"/listings/{listing}/moderate",{"reason":"Cần cập nhật mô tả."}).status_code,200)
    c.eq(c.post("member02",f"/listings/{listing}/buy").status_code,409);c.eq(c.listing_item(listing)["status"],"HIDDEN");c.eq(c.balance("member02"),1500)

@register("FR-14","FLOW03-B: memberđăngnhập → admin khóa → phiênbịthu hồi","Adminlock200;phiêncũ401vàđăngnhậplại401.",kind="E2E",case_id="TC-FLOW03-002",requirements=["FR-01","FR-14"],steps=["member02đăngnhậpvàđọckho.","Adminkhóamember02.","Phiêncũđọckhobị401;đăngnhậplạicũng401."])
def flow_03b(c):
    client,_=c.client("member02");c.eq(c.get("member02","/inventory").status_code,200);c.eq(c.patch("admin","/users/2",{"active":False}).status_code,200)
    response=client.get("/api/inventory");c.capture("GET","/inventory","member02",None,response);c.eq(response.status_code,401);c.eq(c.login("member02","Demo@123").status_code,401)

@register("FR-15","FLOW03-C: adminthêmmodel → sửa giá → memberkiểmtra","Modelmớiđược tạo,sửa vàtra trongcatalog/detailđúnggiámới.",kind="E2E",case_id="TC-FLOW03-003",requirements=["FR-02","FR-03","FR-15"],steps=["Adminthêmmodeltestfloat0.25.","Adminsửareference_price450.","Membertìmtheotênvàkiểmtrachitiếtmodelmới."])
def flow_03c(c):
    response=c.post("admin","/skins",SKIN);c.eq(response.status_code,201);skin=response.json["id"]
    c.eq(c.patch("admin",f"/skins/{skin}",{"reference_price":450}).status_code,200)
    items=c.items("member01","/skins?"+urlencode({"q":"Test Pattern"}));c.truth(skin in [i["id"] for i in items])
    detail=c.get("member01",f"/skins/{skin}");c.eq(detail.status_code,200);c.eq(detail.json.get("item",detail.json)["reference_price"],450)


def json_default(value):
    if isinstance(value,set):return sorted(value)
    if isinstance(value,bytes):return {"bytes":len(value)}
    raise TypeError(type(value).__name__)


def run(mode):
    from app import create_app,initialize
    output=SUB/"evidence"/"functional"/mode
    output.mkdir(parents=True,exist_ok=True)
    hashes={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [ROOT/"app.py",ROOT/"schema.sql"] if path.exists()}
    started=datetime.now(timezone.utc).isoformat()
    results=[]
    with tempfile.TemporaryDirectory(prefix="shiloskin-functional-") as temp:
        root=Path(temp);seed=root/"seed.db"
        app=create_app({"TESTING":True,"DATABASE":str(seed),"TRAINING_BUGS":False})
        initialize(app,demo=True)
        for definition in CASES:
            database=root/(definition["id"]+".db")
            with closing(sqlite3.connect(seed)) as source,closing(sqlite3.connect(database)) as target:source.backup(target)
            app=create_app({"TESTING":True,"DATABASE":str(database),"TRAINING_BUGS":mode=="training","SECRET_KEY":"suite-only-not-server-key","SESSION_COOKIE_SECURE":False})
            check=Check(app);row={k:v for k,v in definition.items() if k!="fn"}
            row.update(mode=mode,executed_at=datetime.now(timezone.utc).isoformat(),scope=SCOPE,
                       responsible_tester=RESPONSIBLE_TESTER,system_owner=SYSTEM_OWNER,execution_operator=EXECUTION_OPERATOR,
                       environment={"runner":"Flask test_client","database":"isolated temporary SQLite","python":sys.version.split()[0]})
            tick=time.perf_counter()
            try:
                definition["fn"](check);row.update(status="PASS",actual="Tất cả assertion đạt; xem trace HTTP và kiểm tra hậu điều kiện.")
            except AssertionError as error:row.update(status="FAIL",actual=str(error))
            except Exception as error:row.update(status="ERROR",actual=f"{type(error).__name__}: {error}",traceback=traceback.format_exc())
            row["duration_ms"]=round((time.perf_counter()-tick)*1000,3);row["trace"]=check.trace
            ops=[step for step in check.trace if "method" in step]
            row["executed_steps"]=[f"{step['actor']}: {step['method']} {step['path']} → {step['http_status']}" for step in ops]
            if not row["data"]:row["data"]={"requests":[{"actor":o["actor"],"method":o["method"],"path":o["path"],"body":o["input"]} for o in ops]}
            row["evidence"]=f"evidence/functional/{mode}/{row['id']}.json"
            (output/(row["id"]+".json")).write_text(json.dumps(row,ensure_ascii=False,indent=2,default=json_default),encoding="utf-8")
            results.append(row);print(f"{mode} {row['id']} {row['status']} {row['title']}",flush=True)
    report={"scope":SCOPE,"mode":mode,"started_at_utc":started,"finished_at_utc":datetime.now(timezone.utc).isoformat(),"source_sha256":hashes,
            "responsible_tester":RESPONSIBLE_TESTER,"system_owner":SYSTEM_OWNER,"execution_operator":EXECUTION_OPERATOR,
            "total":len(results),"counts":{status:sum(row["status"]==status for row in results) for status in ("PASS","FAIL","ERROR")},"cases":results}
    (output/"results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,default=json_default),encoding="utf-8")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=["baseline","training","both"],default="both")
    args=parser.parse_args();(SUB/"data").mkdir(parents=True,exist_ok=True)
    definitions=[{k:v for k,v in c.items() if k!="fn"} for c in CASES]
    (SUB/"data"/"functional_cases.json").write_text(json.dumps(definitions,ensure_ascii=False,indent=2),encoding="utf-8")
    reports=[run(m) for m in (["baseline","training"] if args.mode=="both" else [args.mode])]
    baseline=next((r for r in reports if r["mode"]=="baseline"),None)
    baseline_rows={r["id"]:r for r in baseline["cases"]} if baseline else {}
    dossier=[]
    for row in reports[-1]["cases"]:
        record={k:v for k,v in row.items() if k not in ["trace","traceback"]}
        if row["id"] in baseline_rows:record.update(baseline_status=baseline_rows[row["id"]]["status"],baseline_evidence=baseline_rows[row["id"]]["evidence"])
        dossier.append(record)
    (SUB/"data"/"functional_cases.json").write_text(json.dumps(dossier,ensure_ascii=False,indent=2,default=json_default),encoding="utf-8")
    # Collect actual successful HTTP samples for the API document.
    examples={}
    for row in (baseline or reports[-1])["cases"]:
        for step in row["trace"]:
            if "method" not in step or step["http_status"]>=400:continue
            route=step["path"].split('?')[0]
            action=step["input"].get("action","") if isinstance(step["input"],dict) else ""
            key=step["method"]+" "+route+(" action="+action if action else "")
            examples.setdefault(key,{**step,"source_case":row["id"],"evidence":row["evidence"]})
    (SUB/"evidence"/"functional"/"api_examples.json").write_text(json.dumps(examples,ensure_ascii=False,indent=2,default=json_default),encoding="utf-8")
    for report in reports:print("SUMMARY",report["mode"],report["total"],report["counts"],flush=True)
    return 1 if any(r["counts"].get("FAIL",0) or r["counts"].get("ERROR",0) for r in reports) else 0


if __name__=="__main__":raise SystemExit(main())
