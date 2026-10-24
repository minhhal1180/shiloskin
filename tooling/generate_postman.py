import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
items=[]
def add(name,method,endpoint,code,body=None,tests=()):
 request={"method":method,"url":"{{baseUrl}}"+endpoint,"header":[]}
 if body is not None:request["body"]={"mode":"raw","raw":json.dumps(body,ensure_ascii=False),"options":{"raw":{"language":"json"}}};request["header"].append({"key":"Content-Type","value":"application/json"})
 if method!='GET' and endpoint!='/api/login':request["header"].append({"key":"X-CSRF-Token","value":"{{csrf}}"})
 items.append({"name":name,"request":request,"event":[{"listen":"test","script":{"type":"text/javascript","exec":[f"pm.test('HTTP {code}',()=>pm.response.to.have.status({code}));",*tests]}}]})
add('Reject unauthenticated session','GET','/api/me',401)
add('Login member','POST','/api/login',200,{'username':'{{username}}','password':'{{password}}'},["pm.test('login success',()=>pm.expect(pm.response.json().ok).true);"])
add('Identity and CSRF','GET','/api/me',200,tests=["pm.environment.set('csrf',pm.response.json().csrf);","pm.test('member role',()=>pm.expect(pm.response.json().user.role).eql('MEMBER'));"])
add('Browse skin catalog','GET','/api/skins',200,tests=["pm.test('catalog nonempty',()=>pm.expect(pm.response.json().items.length).above(0));"])
add('Skin detail','GET','/api/skins/1',200,tests=["pm.test('float in valid interval',()=>pm.expect(pm.response.json().item.float_value).within(0,1));"])
add('Own inventory','GET','/api/inventory',200,tests=["pm.test('own inventory ownership',()=>pm.expect(pm.response.json().items.every(i=>i.owner_id===1)).true);"])
add('Public member inventory for trade','GET','/api/inventory?user_id=2',200,tests=["pm.test('target ownership',()=>pm.expect(pm.response.json().items.every(i=>i.owner_id===2)).true);"])
add('Active marketplace','GET','/api/listings?status=ACTIVE',200,tests=["pm.test('active status filter',()=>pm.expect(pm.response.json().items.every(i=>i.status==='ACTIVE')).true);"])
add('Create listing from CSV data','POST','/api/listings',201,{'item_id':'{{item_id}}','price':'{{price}}'},["pm.environment.set('listingId',pm.response.json().id);","pm.test('listing id assigned',()=>pm.expect(pm.response.json().id).a('number'));"])
add('Find own listing','GET','/api/listings?mine=1',200,tests=["pm.test('created listing exists',()=>{const id=Number(pm.environment.get('listingId'));pm.expect(pm.response.json().items.some(i=>i.id===id)).true;});"])
add('Cancel own active listing','POST','/api/listings/{{listingId}}/cancel',200,{})
add('Cancelled listing persists','GET','/api/listings?mine=1',200,tests=["pm.test('cancelled state',()=>pm.expect(pm.response.json().items.find(i=>i.id===Number(pm.environment.get('listingId'))).status).eql('CANCELLED'));"])
add('Reject invalid item ID','POST','/api/listings',400,{'item_id':'bad-id','price':350})
add('Unknown catalog detail returns 404','GET','/api/skins/999999',404)
add('Member cannot access user administration','GET','/api/users',403)
add('Read trade offers','GET','/api/trades',200,tests=["pm.test('trade list',()=>pm.expect(pm.response.json().items).an('array'));"])
add('Read history','GET','/api/history',200,tests=["pm.test('history list',()=>pm.expect(pm.response.json().items).an('array'));"])
add('Read private notifications','GET','/api/notifications',200,tests=["pm.test('notification list',()=>pm.expect(pm.response.json().items).an('array'));"])
add('Logout','POST','/api/logout',200,{})
add('Session revoked after logout','GET','/api/me',401)
collection={"info":{"name":"ShiloSkin — functional API test with three CSV datasets","schema":"https://schema.getpostman.com/json/collection/v2.1.0/collection.json","description":"Actual tests on isolated local copy of the AI-assisted ShiloSkin build. Tester: Bui Xuan Minh 23110193, owner: Nguyen Tu Lan 23110306. Not a blind assessment of an independently developed system."},"item":items}
(ROOT/'shiloskin.postman_collection.json').write_text(json.dumps(collection,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'shiloskin.postman_environment.json').write_text(json.dumps({'name':'ShiloSkin local isolated test','values':[{'key':'baseUrl','value':'http://127.0.0.1:5000','enabled':True}]},indent=2),encoding='utf-8')
