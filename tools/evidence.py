"""Capture genuine HTTP defect traces and labelled report screenshots.

Screenshots show rendered measured HTTP reports, not claimed manual UI actions.
Each seed is reproduced against a fresh temporary app/database. No deployed
accounts, real money or Steam inventory are used or changed.
"""
import hashlib
import html
import http.cookiejar
import json
import math
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SUB=ROOT.parent/"qlychtsv"/"submission"/"partner"
sys.path.insert(0,str(ROOT))
from app import create_app,initialize
from playwright.sync_api import sync_playwright
from playwright.sync_api import expect
from werkzeug.serving import WSGIRequestHandler,make_server

SCOPE="Bùi Xuân Minh – 23110193 chịu trách nhiệm hồ sơ test ShiloSkin của Nguyễn Từ Lân – 23110306; Codex tự động thực thi, biết mã nguồn/các lỗi cài sẵn, không phải test mù độc lập."
SOURCE_HASHES={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
               for name in ["app.py","schema.sql","bugs.py","training_extras.py","static/app.js","static/style.css","static/training.js","static/training.css"]
               if (path:=ROOT/name).exists()}


class Quiet(WSGIRequestHandler):
    def log_request(self,*args,**kwargs):pass


class API:
    def __init__(self,base):
        self.base=base
        self.clients={}
        self.trace=[]

    def call(self,actor,method,path,data=None):
        if actor not in self.clients:
            jar=http.cookiejar.CookieJar()
            opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
            body=json.dumps({"username":actor,"password":"Demo@123"}).encode()
            req=urllib.request.Request(self.base+"/api/login",data=body,headers={"Content-Type":"application/json"})
            with opener.open(req,timeout=20) as response:
                if response.status!=200:raise RuntimeError("Fixture login failed")
            with opener.open(self.base+"/api/me",timeout=20) as response:token=json.load(response)["csrf"]
            self.clients[actor]=(opener,token)
        opener,token=self.clients[actor]
        body=None if method=="GET" else json.dumps(data or {}).encode()
        req=urllib.request.Request(self.base+"/api"+path,data=body,method=method,
                                   headers={"Content-Type":"application/json","X-CSRF-Token":token})
        tick=time.perf_counter()
        try:response=opener.open(req,timeout=20)
        except urllib.error.HTTPError as error:response=error
        status=response.status
        with response:
            body=response.read().decode("utf-8",errors="replace")
            try:body=json.loads(body)
            except json.JSONDecodeError:body={"response_text":body[:2000]}
        if isinstance(body,dict) and "csrf" in body:body={**body,"csrf":"[redacted]"}
        self.trace.append({"actor":actor,"method":method,"path":"/api"+path,"input":data,"http_status":status,"response":body,"duration_ms":round((time.perf_counter()-tick)*1000,3)})
        return status,body

    def get(self,actor,path):return self.call(actor,"GET",path)
    def post(self,actor,path,data=None):return self.call(actor,"POST",path,data)
    def setup_listing(self):
        status,body=self.post("member01","/listings",{"item_id":1,"price":200})
        if status!=201:raise RuntimeError("Setup listing failed")
        return body["id"]
    def setup_trade(self):
        status,body=self.post("member01","/trades",{"give_item_id":1,"want_item_id":7})
        if status!=201:raise RuntimeError("Setup trade failed")
        return body["id"]


def reproduce(seed,api):
    if seed in {"S01","S02"}:
        price=0 if seed=="S01" else 100001
        status,_body=api.post("member01","/listings",{"item_id":1,"price":price})
        api.get("member01","/listings?mine=1")
        return "Giá listing phải là số nguyên1..100000; dữ liệu sai trả400, không tạo listing.",status==400,{"input_price":price,"actual_http":status},["member01 đăng nhập.",f"Gửi item_id1,price={price} tới POST/listings.","Đọc danh sách tin của chính mình để xác nhận kết quả."]
    if seed=="S03":
        listing=api.setup_listing();status,_=api.post("member01",f"/listings/{listing}/buy");api.get("member01","/listings?mine=1")
        return "Người bán không được tự mua; trả409 và giữ ACTIVE.",status==409,{"listing_id":listing,"actual_http":status},["member01 tạo listing item1.","member01 gọi buy chính listing đó.","Đối chiếu status và tin của mình."]
    if seed=="S04":
        status,_=api.post("member01","/listings/2/buy");_,me=api.get("member01","/me")
        return "Balance1000 không đủ mua listing2200; trả409, không âm coins.",status==409,{"actual_http":status,"balance_after":me["user"]["balance"]},["member01 có1000coins.","Mua listing2giá2200.","Kiểm tra HTTP và số dư sau giao dịch."]
    if seed=="S05":
        status,_=api.post("member01","/listings/1/buy")
        if status!=200:raise RuntimeError("Setup buy failed")
        status,_=api.post("member02","/listings/1/cancel");_,items=api.get("member02","/listings?mine=1")
        item=next(i for i in items["items"] if i["id"]==1)
        return "Listing SOLD không được hủy; trả409 và giữ SOLD.",status==409,{"actual_http":status,"listing_status":item["status"]},["member01 mua listing1.","Seller member02 hủy listing đã SOLD.","Đối chiếu tin bán của member02."]
    if seed=="S06":
        trade=api.setup_trade();status,_=api.post("member02",f"/trades/{trade}/action",{"action":"reject"})
        if status!=200:raise RuntimeError("Setup reject failed")
        status,_=api.post("member02",f"/trades/{trade}/action",{"action":"accept"});_,items=api.get("member02","/trades")
        item=next(i for i in items["items"] if i["id"]==trade)
        return "Chỉ PENDING được accept; REJECTED phải409, không đổi item.",status==409,{"actual_http":status,"trade_status":item["status"]},["member01 offer item1lấy7.","member02 reject offer.","member02 accept lại offer REJECTED; xem kết quả."]
    if seed=="S07":
        body={"name":"AK-47 | Defect proof","weapon":"AK-47","rarity":"Restricted","wear":"Field-Tested","float_value":1.2,"reference_price":250}
        status,result=api.post("admin","/skins",body)
        if status==201:api.get("admin",f'/skins/{result["id"]}')
        return "Float skin phải hữu hạn trong[0,1]; float1.2 trả400.",status==400,{"input_float":1.2,"actual_http":status},["Admin đăng nhập.","Tạo model với float_value1.2 và các trường còn lại hợp lệ.","Đọc model vừa được tạo nếu server chấp nhận."]
    if seed=="S08":
        status,_=api.post("moderator01","/listings/1/moderate",{"reason":""});_,items=api.get("moderator01","/listings")
        item=next(i for i in items["items"] if i["id"]==1)
        return "Moderator phải ghi lý do không rỗng; reason rỗng trả400, giữ ACTIVE.",status==400,{"actual_http":status,"listing_status":item["status"],"moderation_reason":item["moderation_reason"]},["Moderator đăng nhập.","Ẩn listing1với reason rỗng.","Kiểm tra trạng thái và lý do trên listing."]
    if seed=="S09":
        _,items=api.get("member01","/notifications");item=items["items"][0]
        status,_=api.post("member01",f'/notifications/{item["id"]}/read');_,updated=api.get("member01","/notifications")
        found=next(i for i in updated["items"] if i["id"]==item["id"])
        return "Đánh dấu đã đọc phải được lưu; tải lại is_read=1.",found["is_read"]==1,{"read_http":status,"is_read_after_refresh":found["is_read"]},["member01 đọc thông báo WELCOME chưa đọc.","POST/read thông báo.","GET lại và đối chiếu is_read."]
    if seed=="S10":
        status,_=api.post("member01","/listings/1/buy")
        if status!=200:raise RuntimeError("Setup buy failed")
        _,items=api.get("member01","/history")
        actions=[i["action"] for i in items["items"]]
        return "Mua thành công phải có BUY audit cho hai bên.","BUY" in actions,{"buy_http":status,"buyer_history_actions":actions},["member01 mua listing1 thành công.","GET/history của buyer.","Tìm sự kiện BUY tương ứng giao dịch."]
    raise ValueError(seed)


def report_html(result):
    actual=html.escape(json.dumps(result["actual"],ensure_ascii=False,indent=2))
    trace=html.escape(json.dumps(result["http_capture"],ensure_ascii=False,indent=2))
    return f'''<!doctype html><html lang="vi"><meta charset="utf-8"><title>{result['id']} HTTP evidence</title>
<style>body{{font-family:Arial,sans-serif;margin:35px;color:#162a3a;background:#f2f6f9}}main{{max-width:1350px;margin:auto;background:white;padding:30px;border-radius:14px}}h1{{color:#984335}}p{{line-height:1.6}}pre{{white-space:pre-wrap;word-break:break-word;font-size:13px;line-height:1.5;background:#edf2f6;padding:18px;border-radius:8px}}.label{{padding:12px;background:#fff3dc;color:#644710}}small{{color:#607586}}</style>
<main><h1>{result['id']} · {html.escape(result['title'])}</h1><p class="label">ẢNH BÁO CÁO HTTP THỰC ĐO — không phải ảnh thao tác giao diện bằng tay. Dữ liệu lấy nguyên từ request/response trên database tạm.</p>
<p><strong>Expected:</strong> {html.escape(result['expected'])}</p><p><strong>Test result:</strong> {result['status']} · TRAINING_BUGS=1</p><h2>Actual</h2><pre>{actual}</pre><h2>Request / response capture</h2><pre>{trace}</pre><small>{html.escape(result['executed_at'])} · {html.escape(SCOPE)}</small></main></html>'''


def main():
    out=SUB/"evidence"/"seeded_functional";out.mkdir(parents=True,exist_ok=True)
    labels={"S01":"Chấp nhận giá listing bằng0", "S02":"Chấp nhận giá listing vượt100000", "S03":"Cho người bán tự mua listing của mình",
            "S04":"Cho mua khi không đủ coins", "S05":"Cho hủy listing đã SOLD", "S06":"Cho accept trade đã REJECTED",
            "S07":"Admin tạo skin có float_value vượt1", "S08":"Moderator ẩn tin không có lý do", "S09":"Đánh dấu đã đọc không lưu", "S10":"Mua thành công không ghi audit BUY"}
    results=[];started=datetime.now(timezone.utc).isoformat()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel="msedge")
        page=browser.new_page(viewport={"width":1440,"height":1100})
        try:
            for seed,title in labels.items():
                with tempfile.TemporaryDirectory(prefix="shiloskin-proof-") as temp:
                    app=create_app({"DATABASE":str(Path(temp)/"proof.db"),"TRAINING_BUGS":True,"TESTING":False,"SESSION_COOKIE_SECURE":False})
                    initialize(app,demo=True)
                    server=make_server("127.0.0.1",0,app,threaded=True,request_handler=Quiet)
                    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                    api=API(f"http://127.0.0.1:{server.server_port}")
                    try:
                        expected,passed,actual,steps=reproduce(seed,api)
                        result={"id":seed,"title":title,"category":"Functional","status":"PASS" if passed else "FAIL","expected":expected,"actual":actual,"steps":steps,
                                "executed_at":datetime.now(timezone.utc).isoformat(),"scope":SCOPE,"responsible_tester":"Bùi Xuân Minh – 23110193","system_owner":"Nguyễn Từ Lân – 23110306",
                                "execution_operator":"Codex automation","training_bugs":True,"http_capture":api.trace,
                                "evidence_type":"Ảnh render báo cáo HTTP được thực đo; không giả là thao tác UI thủ công.","screenshot":f"{seed}-http-report.png"}
                        page.set_content(report_html(result))
                        page.screenshot(path=str(out/result["screenshot"]),full_page=True)
                        result["screenshot_sha256"]=hashlib.sha256((out/result["screenshot"]).read_bytes()).hexdigest()
                        (out/f"{seed}.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
                        results.append(result);print(seed,result["status"],actual,flush=True)
                    finally:
                        server.shutdown();server.server_close();thread.join(timeout=5)
        finally:browser.close()
    errors=[r for r in results if r["status"]!="FAIL"]
    report={"started_at_utc":started,"finished_at_utc":datetime.now(timezone.utc).isoformat(),"scope":SCOPE,
            "source_sha256":SOURCE_HASHES,
            "summary":{"total":len(results),"counts":dict(Counter(r["status"] for r in results)),"verification":"PASS" if len(results)==10 and not errors else "FAIL"},"results":results}
    (out/"results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("VERIFICATION",report["summary"],flush=True)
    return 0 if report["summary"]["verification"]=="PASS" else 1


def capture_ui():
    """Compare six real UI defects, four HTTP defects, and three exploratory cases."""
    out=SUB/"evidence"/"additional";out.mkdir(parents=True,exist_ok=True)
    exp_out=SUB/"evidence"/"exploratory";exp_out.mkdir(parents=True,exist_ok=True)
    labels={"V01":("Visual","NFR-04","Tên skin bị cắt ở desktop"),"V02":("Visual","NFR-04","Hộp thoại đăng bán tràn màn hình375px"),
            "V03":("Visual","NFR-04","Nhãn rarity bị ẩn trên mobile"),"C01":("Content","NFR-05","ACCEPTED hiển thị nhầm Đã từ chối"),
            "C02":("Content","NFR-05","Giá mô phỏng hiển thị ký hiệu đôla thay SC"),"C03":("Content","NFR-05","Hướng dẫn float ghi sai khoảng0..10"),
            "P01":("Performance","NFR-01","Tìm skin vượt800ms"),"P02":("Performance","NFR-02","Thông báo vượt900ms"),
            "R01":("Crash","NFR-08","Skin không tồn tại gâyHTTP500"),"R02":("Crash","NFR-08","Giá không phải số gâyHTTP500")}
    rows=[];findings=[];started=datetime.now(timezone.utc).isoformat()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel="msedge")
        try:
            for mode in ["baseline","training"]:
                with tempfile.TemporaryDirectory(prefix="shilo-ui-proof-") as temp:
                    app=create_app({"DATABASE":str(Path(temp)/"ui.db"),"TRAINING_BUGS":mode=="training","SESSION_COOKIE_SECURE":False})
                    initialize(app,demo=True)
                    server=make_server("127.0.0.1",0,app,threaded=True,request_handler=Quiet)
                    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                    base=f"http://127.0.0.1:{server.server_port}";api=API(base)
                    contexts=[]
                    def login(actor="member01",viewport=None):
                        context=browser.new_context(viewport=viewport or {"width":1440,"height":1100});contexts.append(context)
                        page=context.new_page();page.goto(base,wait_until="domcontentloaded")
                        page.locator('#login-form [name=username]').fill(actor);page.locator('#login-form [name=password]').fill('Demo@123')
                        page.locator('#login-form button[type=submit]').click();expect(page.locator('#workspace')).to_be_visible()
                        expect(page.locator('#main h1')).to_be_visible()
                        return page
                    def go(page,target):
                        page.goto(base+'/#'+target,wait_until="domcontentloaded")
                        expect(page.locator('#main h1')).to_be_visible()
                    def store(identifier,expected,actual,passed,page,steps,report=False):
                        category,requirement,title=labels[identifier]
                        record={"id":identifier,"title":title,"category":category,"requirement":requirement,"mode":mode,"training_bugs":mode=="training",
                                "status":"PASS" if passed else "FAIL","expected":expected,"actual":actual,"steps":steps,"scope":SCOPE,
                                "executed_at":datetime.now(timezone.utc).isoformat(),"http_capture":api.trace[:] if report else [],
                                "evidence_type":"Ảnh báo cáo HTTP thực đo; không giả UI" if report else "Ảnh UI và DOM từ trình duyệt thực chạy"}
                        screenshot=f"{identifier}-{mode}.png"
                        if report:page.set_content(report_html({**record,"http_capture":api.trace}))
                        page.screenshot(path=str(out/screenshot),full_page=True);record["evidence_files"]=[screenshot,f"{identifier}-{mode}.json"]
                        (out/f"{identifier}-{mode}.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
                        rows.append(record);print(mode,identifier,record["status"],actual,flush=True)
                    try:
                        page=login();go(page,'catalog')
                        heading=page.locator('.skin-name').filter(has=page.locator('[data-skin="9"]'))
                        expect(heading).to_be_visible()
                        actual=heading.evaluate("e=>({text:e.textContent,client:e.clientWidth,scroll:e.scrollWidth,overflow:getComputedStyle(e).overflow,white_space:getComputedStyle(e).whiteSpace})")
                        store("V01","Tên skin ở desktop hiển thị đầy đủ, không bị cắt im lặng.",actual,actual['scroll']<=actual['client']+1,page,["Desktop1440×1100; member01 đăng nhập và mở danh mục.","Đọc tên Mecha Industries (model9), đo scrollWidth/clientWidth của tiêu đề."])
                        go(page,'market')
                        actual={"currency_labels":page.locator('.currency-text').all_text_contents()}
                        store("C02","Giá điểm mô phỏng dùng SC, không gợi ý đôla/tiền thật.",actual,all(value.strip()=='SC' for value in actual['currency_labels']),page,["Mở chợ skin với member01.","Đọc các ký hiệu tiền trong giá skin."])
                        page.locator('[data-skin]').first.click();expect(page.locator('#detail-dialog')).to_be_visible()
                        actual={"float_help":page.locator('#detail-dialog .float-help').inner_text()}
                        store("C03","Hướng dẫn phải ghi float trong khoảng0đến1.",actual,actual['float_help'].strip()=='Float nằm trong khoảng 0 đến 1.',page,["Mở chi tiết skin.","Đọc dòng hướng dẫn float và đối chiếu giới hạn backend[0,1]."])
                        page.locator('#detail-dialog [data-close]').click()
                        page.set_viewport_size({"width":375,"height":812})
                        actual=page.locator('.skin-meta .rarity-badge').first.evaluate("e=>({text:e.textContent,visibility:getComputedStyle(e).visibility,display:getComputedStyle(e).display})")
                        store("V03","Rarity vẫn nhìn thấy trên viewport375px.",actual,actual['visibility']=='visible' and actual['display']!='none',page,["Viewport375×812; mở chợ skin.","Kiểm tra nhãn rarity trên thẻ skin."])
                        go(page,'inventory');page.locator('[data-sell="1"]').click();expect(page.locator('#sell-dialog')).to_be_visible()
                        actual=page.locator('#sell-dialog').evaluate("e=>({viewport:innerWidth,width:e.getBoundingClientRect().width,left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right})")
                        store("V02","Hộp thoại bán nằm trong viewport375px.",actual,actual['width']<=actual['viewport'] and actual['right']<=actual['viewport'],page,["Viewport375×812.","Mở kho member01 rồi Đăng bán item1.","Đo bounding box của hộp thoại."])
                        # V02 intentionally pushes the close button outside the viewport.
                        # Escape is a normal user action that lets the remaining cases run.
                        page.keyboard.press('Escape')
                        trade=api.setup_trade();status,_=api.post('member02',f'/trades/{trade}/action',{'action':'accept'})
                        if status!=200:raise RuntimeError('Content case setup trade accept failed')
                        page.set_viewport_size({"width":1440,"height":1100});go(page,'trades')
                        expect(page.locator('.trade-card')).to_be_visible()
                        actual={"api_status":"ACCEPTED","display_label":page.locator('.trade-card .status-badge').first.inner_text()}
                        store("C01","ACCEPTED phải hiển thị Đã chấp nhận.",actual,actual['display_label']=='Đã chấp nhận',page,["Tạo và chấp nhận trade hợp lệ bằng API.","Mở trang trao đổi của member01, đối chiếu nhãn ACCEPTED."])
                        api.get('member01','/me')
                        for identifier,endpoint,limit in [('P01','/skins?q=AK',800),('P02','/notifications',900)]:
                            samples=[];statuses=[]
                            for _ in range(5):
                                status,_=api.get('member01',endpoint);statuses.append(status);samples.append(api.trace[-1]['duration_ms'])
                            actual={"endpoint":"/api"+endpoint,"samples_ms":samples,"p95_ms":sorted(samples)[math.ceil(.95*len(samples))-1],"threshold_ms":limit,"http_statuses":statuses,"users":1}
                            store(identifier,f"5mẫu tuần tự một người dùng: p95≤{limit}ms; không gọi phép thử này là kiểm thử tải.",actual,all(s==200 for s in statuses) and actual['p95_ms']<=limit,page,["Đăng nhập trước khi đo.",f"Gửi5requestGET{endpoint}, đo đủbody.","Tính p95 nearest-rank và đối chiếu ngưỡng."],True)
                        status,body=api.get('member01','/skins/999999');health,_=api.get('member01','/me')
                        actual={"endpoint":"GET/api/skins/999999","http_status":status,"response":body,"health_after":health}
                        store('R01','Skin không tồn tại trả404; /me sau lỗi vẫn200.',actual,status==404 and health==200,page,["member01 gọi skin ID999999 không tồn tại.","ĐọcHTTPstatus rồi kiểm tra/me."],True)
                        status,body=api.post('member01','/listings',{'item_id':2,'price':'abc'});health,_=api.get('member01','/me')
                        actual={"endpoint":"POST/api/listings","http_status":status,"response":body,"input_price":"abc","health_after":health}
                        store('R02','Giá không phải số trả400; /me sau lỗi vẫn200.',actual,status==400 and health==200,page,["member01 gửiitem2priceabc.","ĐọcHTTPstatus rồi kiểm tra/me."],True)
                    finally:
                        for context in contexts:context.close()
                        server.shutdown();server.server_close();thread.join(timeout=5)
            # Exploratory cases use baseline, confirming they are not injected extras.
            with tempfile.TemporaryDirectory(prefix="shilo-exploratory-") as temp:
                app=create_app({"DATABASE":str(Path(temp)/"exp.db"),"TRAINING_BUGS":False,"SESSION_COOKIE_SECURE":False});initialize(app,demo=True)
                server=make_server('127.0.0.1',0,app,threaded=True,request_handler=Quiet);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                base=f'http://127.0.0.1:{server.server_port}';api=API(base)
                context=browser.new_context(viewport={"width":390,"height":844});page=context.new_page()
                def signin(actor):
                    page.locator('#login-form [name=username]').fill(actor);page.locator('#login-form [name=password]').fill('Demo@123');page.locator('#login-form button[type=submit]').click();expect(page.locator('#workspace')).to_be_visible();expect(page.locator('#main h1')).to_be_visible()
                def exp_store(identifier,title,expected,actual,passed,steps,screenshots):
                    record={"id":identifier,"title":title,"category":"Visual" if identifier=='X03' else 'Functional',"training_bugs":False,"seeded":False,"status":"PASS" if passed else "FAIL",
                            "expected":expected,"actual":actual,"steps":steps,"screenshots":screenshots,"source":"Tiêu chí usability khám phá ngoài đặc tả gốc; không giả là yêu cầu đã có.","scope":SCOPE,"executed_at":datetime.now(timezone.utc).isoformat()}
                    findings.append(record);print('exploratory',identifier,record['status'],actual,flush=True)
                try:
                    page.goto(base);signin('member01');page.locator('#market-filter [name=q]').fill('PRIVATE_QUERY_X01');page.locator('#market-filter button').click()
                    expect(page.locator('.skin-card')).to_have_count(0);page.screenshot(path=str(exp_out/'X01-before.png'),full_page=True)
                    page.locator('#logout').click();expect(page.locator('#login-screen')).to_be_visible();signin('member02')
                    actual={"current_user":"member02","inherited_query":page.locator('#market-filter [name=q]').input_value(),"visible_cards":page.locator('.skin-card').count()}
                    page.screenshot(path=str(exp_out/'X01-after.png'),full_page=True)
                    exp_store('X01','Bộ lọc của tài khoản trước giữ lại sau khi đổi tài khoản','Đổi tài khoản phải đặt lại bộ lọc cá nhân.',actual,actual['inherited_query']=='',["member01 tìmPRIVATE_QUERY_X01.","Đăng xuất và đăng nhập member02 trong cùng tab.","Quan sát ô tìm kiếm và danh sách."],['X01-before.png','X01-after.png'])
                    page.goto(base+'/#inventory');expect(page.locator('[data-sell="7"]')).to_be_visible();page.locator('[data-sell="7"]').click();expect(page.locator('#sell-dialog')).to_be_visible()
                    page.locator('#sell-form [name=price]').fill('321');page.screenshot(path=str(exp_out/'X02-before.png'),full_page=True)
                    page.keyboard.press('Escape');expect(page.locator('#sell-dialog')).not_to_be_visible();page.locator('[data-sell="7"]').click();expect(page.locator('#sell-dialog')).to_be_visible()
                    actual={"draft_price_before":"321","draft_price_after":page.locator('#sell-form [name=price]').input_value(),"submitted":False}
                    page.screenshot(path=str(exp_out/'X02-after.png'),full_page=True)
                    exp_store('X02','Đóng bằng Escape làm mất bản nháp giá bán','Không có xác nhận bỏ thì mở lại phải còn bản nháp cùng phiên.',actual,actual['draft_price_after']=='321',["member02 mở bánitem7, nhập321 chưa gửi.","Escapeđóng; mở lại cùngitem.","Quan sát giá bị reset."],['X02-before.png','X02-after.png'])
                    page.locator('#sell-dialog [data-close]').first.click()
                    page.goto(base+'/#catalog');expect(page.locator('[data-skin="1"]').first).to_be_visible();page.locator('[data-skin="1"]').first.click();expect(page.locator('#detail-dialog')).to_be_visible()
                    page.screenshot(path=str(exp_out/'X03-before.png'),full_page=True);page.locator('#detail-dialog [data-close]').click()
                    status,_=api.call('admin','PATCH','/skins/1',{'name':'W'*120})
                    if status!=200:raise RuntimeError('Exploratory long name fixture failed')
                    page.goto(base+'/#catalog');expect(page.locator('[data-skin="1"]').first).to_be_visible();page.locator('[data-skin="1"]').first.click();expect(page.locator('#detail-dialog')).to_be_visible()
                    actual=page.locator('#skin-detail .meta-value').evaluate("e=>({length:e.textContent.length,client:e.clientWidth,scroll:e.scrollWidth,viewport:innerWidth,overflowWrap:getComputedStyle(e).overflowWrap,modalScroll:document.querySelector('#detail-dialog').scrollWidth,modalClient:document.querySelector('#detail-dialog').clientWidth})")
                    page.screenshot(path=str(exp_out/'X03-after.png'),full_page=True)
                    exp_store('X03','Tên skin hợp lệ120ký tự liền nhau gây tràn metadata','Giá trị tên hợp lệ phải xuống dòng trong modal mobile, không cần cuộn ngang.',actual,actual['scroll']<=actual['client']+1,["Viewport390×844; mở model1bình thường.","Admin đổi tên model1thành120chữW hợp lệ.","Mở lại chi tiết và đo scrollWidth/clientWidth metadata."],['X03-before.png','X03-after.png'])
                finally:
                    context.close();server.shutdown();server.server_close();thread.join(timeout=5)
        finally:browser.close()
    counts={mode:dict(Counter(r['status'] for r in rows if r['mode']==mode)) for mode in ['baseline','training']}
    report={"started_at_utc":started,"finished_at_utc":datetime.now(timezone.utc).isoformat(),"scope":SCOPE,"source_sha256":SOURCE_HASHES,"summary":counts,"results":rows}
    (out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    exp_report={"scope":SCOPE,"training_bugs":False,"source_sha256":SOURCE_HASHES,"findings":findings,"summary":dict(Counter(r['status'] for r in findings))}
    (exp_out/'results.json').write_text(json.dumps(exp_report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('UI_SUMMARY',counts,'EXPLORATORY',exp_report['summary'],flush=True)
    return 0 if counts=={'baseline':{'PASS':10},'training':{'FAIL':10}} and exp_report['summary']=={'FAIL':3} else 1


if __name__=="__main__":raise SystemExit(capture_ui() if '--ui' in sys.argv else main())
