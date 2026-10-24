'use strict';
const $=(selector,root=document)=>root.querySelector(selector);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ROLE={MEMBER:'Thành viên',MODERATOR:'Kiểm duyệt viên',ADMIN:'Quản trị viên'};
const STATUS={ACTIVE:'Đang bán',SOLD:'Đã bán',CANCELLED:'Đã hủy',HIDDEN:'Đã ẩn',PENDING:'Chờ phản hồi',ACCEPTED:'Đã chấp nhận',REJECTED:'Đã từ chối'};
const COLORS={'Consumer Grade':'#b0c3d9','Industrial Grade':'#7eacdf','Mil-Spec':'#6589df',Restricted:'#9c7ade',Classified:'#d273c3',Covert:'#e28b7a'};
const RARITIES=Object.keys(COLORS);
let DISPLAY_CURRENCY='SC';
let user=null,csrf='',activePage='',renderVersion=0,toastTimer;
let ownInventory=[],tradeUsers=[],catalogItems=[],userItems=[];
const filters={marketQ:'',catalogQ:'',rarity:'',weapon:'',inventoryQ:'',tradeStatus:'',mine:false};
const money=value=>`${Number(value||0).toLocaleString('vi-VN')} <small class="currency-text">${DISPLAY_CURRENCY}</small>`;
const time=value=>value?new Date(value).toLocaleString('vi-VN'):'—';
const rarityClass=value=>'rarity-'+String(value||'').toLowerCase().replace(/[^a-z0-9]+/g,'-');
const badge=status=>`<span class="status-badge ${esc(status)}">${esc(STATUS[status]||status)}</span>`;
function toast(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,4500);}
async function api(path,options={}){
  const init={...options,headers:{...options.headers}};
  if(init.method&&init.method!=='GET'){
    init.headers['X-CSRF-Token']=csrf;
    init.headers['Content-Type']='application/json';
    init.body=JSON.stringify(init.body||{});
  }
  const response=await fetch('/api'+path,init);
  let data;try{data=await response.json();}catch{throw new Error('Máy chủ chưa trả dữ liệu hợp lệ. Vui lòng thử lại.');}
  if(!response.ok){if(response.status===401&&path!=='/login')showLogin();throw new Error(data.error||'Không thể thực hiện thao tác.');}
  return data;
}
function showLogin(){user=null;csrf='';renderVersion++;$('#workspace').hidden=true;$('#login-screen').hidden=false;$('#main').replaceChildren();document.querySelectorAll('dialog[open]').forEach(d=>d.close());}
function header(title,description,action=''){return `<div class="breadcrumb">ShiloSkin / ${esc(title)}</div><div class="page-heading"><div><span class="eyebrow">COLLECTION EXCHANGE</span><h1>${esc(title)}</h1><p>${esc(description)}</p></div>${action}</div>`;}
function empty(title,description){return `<div class="panel empty"><span class="empty-symbol">◇</span><strong>${esc(title)}</strong>${esc(description)}</div>`;}
function go(page){if(location.hash==='#'+page)route();else location.hash=page;}
function navItem(page,icon,title){return `<button class="nav-item ${activePage===page?'active':''}" data-nav="${page}"><span class="nav-icon" aria-hidden="true">${icon}</span>${title}</button>`;}
function navigation(){
  const menus=user.role==='ADMIN'?[['catalog','▦','Danh mục skin'],['users','♙','Tài khoản'],['history','◷','Lịch sử'],['notifications','♧','Thông báo']]:user.role==='MODERATOR'?[['moderation','▤','Kiểm duyệt tin'],['catalog','▦','Danh mục skin'],['history','◷','Lịch sử'],['notifications','♧','Thông báo']]:[['market','▦','Chợ skin'],['catalog','▧','Thư viện skin'],['inventory','◇','Kho vật phẩm'],['trades','⇄','Đề nghị trao đổi'],['history','◷','Lịch sử giao dịch'],['notifications','♧','Thông báo']];
  $('#navigation').innerHTML=menus.map(item=>navItem(...item)).join('');
  document.querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>go(b.dataset.nav));
}
async function updateWallet(){const current=await api('/me');user=current.user;csrf=current.csrf;$('#balance').textContent=Number(user.balance||0).toLocaleString('vi-VN');}
async function boot(){
  const current=await api('/me');user=current.user;csrf=current.csrf;
  $('#login-screen').hidden=true;$('#workspace').hidden=false;
  $('#user-name').textContent=user.name;$('#user-role').textContent=ROLE[user.role];
  $('#avatar').textContent=user.name.split(' ').slice(-2).map(v=>v[0]).join('').toUpperCase();
  $('#balance').textContent=Number(user.balance||0).toLocaleString('vi-VN');
  await route();
}
async function route(){
  if(!user)return;
  const version=++renderVersion;
  const allowed=user.role==='ADMIN'?['catalog','users','history','notifications']:user.role==='MODERATOR'?['moderation','catalog','history','notifications']:['market','catalog','inventory','trades','history','notifications'];
  const requested=location.hash.slice(1)||allowed[0];
  activePage=allowed.includes(requested)?requested:allowed[0];navigation();
  $('#main').innerHTML='<p class="muted">Đang tải dữ liệu…</p>';
  try{
    if(activePage==='market'||activePage==='moderation')await renderMarket(version);
    else if(activePage==='catalog')await renderCatalog(version);
    else if(activePage==='inventory')await renderInventory(version);
    else if(activePage==='trades')await renderTrades(version);
    else if(activePage==='history')await renderHistory(version);
    else if(activePage==='notifications')await renderNotifications(version);
    else if(activePage==='users')await renderUsers(version);
  }catch(error){if(version===renderVersion&&user){$('#main').innerHTML=empty('Chưa thể tải dữ liệu',error.message);toast(error.message);}}
}
function gunSVG(weapon,rarity){
  const color=COLORS[rarity]||'#a5b0c4';
  const pistol=/USP|Glock|Desert|P250/i.test(weapon||'');
  const silhouette=pistol?'<path d="M97 68h242v35H214l-28 88h-56l26-90H97z"/><path d="M220 104h71v28h-76z" opacity=".65"/><rect x="340" y="76" width="43" height="18" rx="3"/>':'<path d="M30 86 116 71 151 90 260 81 274 64h80l14 24h117v17l-121 5-31 23h-49l-22 35-31-10 15-32-85-10-28 30-22-13 17-22-90 9z"/><path d="M278 132h42l-12 64-33-11z" opacity=".8"/><rect x="481" y="89" width="54" height="14" rx="3"/><path d="M355 54h29v12h-29z" opacity=".7"/>';
  return `<svg viewBox="0 0 ${pistol?'480':'560'} 230" aria-hidden="true"><g fill="${color}">${silhouette}</g><path d="${pistol?'M113 79h210M132 86h152':'M52 98 109 90 136 99M165 99h78M379 95h86'}" stroke="#192333" stroke-width="9"/><path d="${pistol?'M157 119h31M151 137h29':'M289 141h21M286 153h21M284 164h19'}" stroke="#131c29" stroke-width="5"/><path d="${pistol?'M127 72h53':'M178 88 244 83'}" stroke="#ffffff45" stroke-width="3"/></svg>`;
}
function rarityBadge(rarity){return `<span class="rarity-badge ${rarityClass(rarity)}">${esc(rarity||'Skin')}</span>`;}
function skinCard(item,kind,index){
  const name=item.skin_name||item.name;
  const skinId=kind==='catalog'?item.id:item.skin_id;
  let actions=`<button class="secondary" ${skinId?`data-skin="${skinId}"`:'disabled'}>Chi tiết ↗</button>`;
  if(kind==='inventory'&&user.role==='MEMBER')actions+=item.locked?'<button disabled>Đang được giữ</button>':`<button class="primary" data-sell="${item.item_id||item.id}">Đăng bán</button>`;
  if(kind==='market'&&item.status==='ACTIVE'){
    if(user.role==='MEMBER'&&item.seller_id!==user.id)actions+=`<button class="primary" data-buy="${item.id}">Mua skin</button>`;
    else if(user.role==='MEMBER'&&item.seller_id===user.id)actions+=`<button data-cancel-listing="${item.id}">Hủy tin</button>`;
    else if(user.role==='MODERATOR')actions+=`<button class="danger" data-moderate="${item.id}">Ẩn tin</button>`;
  }
  if(kind==='catalog'&&user.role==='ADMIN')actions+=`<button class="primary" data-edit-skin="${item.id}">Sửa skin</button>`;
  return `<article class="skin-card ${rarityClass(item.rarity)}"><div class="skin-art"><span class="art-index">${esc(item.weapon)} / ${String(index+1).padStart(2,'0')}</span>${gunSVG(item.weapon,item.rarity)}<span class="art-float">FLOAT ${Number(item.float_value||0).toFixed(4)}</span></div><div class="skin-card-content"><div class="skin-weapon">${esc(item.weapon)}</div><h3 class="skin-name">${skinId?`<button class="skin-name-button" data-skin="${skinId}">${esc(name)}</button>`:esc(name)}</h3><div class="skin-meta">${rarityBadge(item.rarity)}<span>${esc(item.wear)}</span></div><div class="skin-price-row"><strong class="skin-price">${money(kind==='market'?item.price:item.reference_price)}</strong><span class="skin-seller">${kind==='market'?esc(item.seller_name||'')+'<br>'+badge(item.status):kind==='inventory'?(item.locked?'Đang được giữ':'Vật phẩm của bạn'):(item.active?'Giá tham khảo':'Đã ngừng hiển thị')}</span></div><div class="card-actions">${actions}</div></div></article>`;
}
async function renderMarket(version){
  const moderation=activePage==='moderation';
  const query=new URLSearchParams({q:filters.marketQ,mine:filters.mine?'1':'0'});
  if(!moderation)query.set('status','ACTIVE');
  const {items}=await api('/listings?'+query);if(version!==renderVersion)return;
  $('#main').innerHTML=header(moderation?'Kiểm duyệt tin đăng':'Chợ skin',moderation?'Theo dõi tin đăng và xử lý nội dung không phù hợp.':'Tìm một điểm nhấn mới cho bộ sưu tập của bạn.',!moderation?'<button class="primary" id="go-inventory">＋ Đăng bán skin</button>':'')
    +(!moderation?`<section class="collection-banner"><div><span class="eyebrow">CURATED FOR YOUR NEXT GAME</span><h2>Thêm cá tính vào từng lựa chọn.</h2><p>Khám phá các tin đăng từ cộng đồng. Mọi giao dịch sử dụng điểm SC mô phỏng.</p></div><div class="banner-number">${items.length.toString().padStart(2,'0')}<small>SKIN ĐANG CHỜ BẠN</small></div></section>`:'')
    +`<form class="filterbar" id="market-filter"><input name="q" aria-label="Tìm skin" placeholder="⌕  Tìm tên skin hoặc vũ khí…" value="${esc(filters.marketQ)}">${!moderation?`<select name="mine" aria-label="Tin đăng"><option value="0" ${!filters.mine?'selected':''}>Tất cả tin đăng</option><option value="1" ${filters.mine?'selected':''}>Tin đăng của tôi</option></select>`:''}<button type="submit">Tìm kiếm</button><span class="result-count">${items.length} tin đăng</span></form>`
    +(items.length?`<div class="skin-grid">${items.map((item,index)=>skinCard(item,'market',index)).join('')}</div>`:empty('Chưa có tin đăng phù hợp','Thử từ khóa khác hoặc đăng bán từ kho vật phẩm của bạn.'));
  if(!moderation)$('#go-inventory').onclick=()=>go('inventory');
  $('#market-filter').onsubmit=event=>{event.preventDefault();const f=new FormData(event.target);filters.marketQ=f.get('q');filters.mine=f.get('mine')==='1';route();};
  bindCards(items);
}
async function renderCatalog(version){
  const params=new URLSearchParams({q:filters.catalogQ,rarity:filters.rarity,weapon:filters.weapon});
  const data=await api('/skins?'+params);if(version!==renderVersion)return;catalogItems=data.items;
  $('#main').innerHTML=header('Danh mục skin','Thông tin vũ khí, độ hiếm, float và giá tham khảo của từng skin.',user.role==='ADMIN'?'<button class="primary" id="new-skin">＋ Thêm skin</button>':'')
    +`<form class="filterbar" id="catalog-filter"><input name="q" aria-label="Tìm danh mục" placeholder="⌕  Tìm skin hoặc vũ khí…" value="${esc(filters.catalogQ)}"><select name="rarity" aria-label="Độ hiếm"><option value="">Tất cả độ hiếm</option>${RARITIES.map(r=>`<option ${r===filters.rarity?'selected':''}>${esc(r)}</option>`).join('')}</select><input name="weapon" aria-label="Lọc vũ khí" placeholder="Vũ khí, ví dụ AK-47" value="${esc(filters.weapon)}"><button type="submit">Lọc</button><span class="result-count">${data.items.length} skin</span></form>`
    +(data.items.length?`<div class="skin-grid">${data.items.map((item,index)=>skinCard(item,'catalog',index)).join('')}</div>`:empty('Chưa có skin phù hợp','Thử đổi từ khóa hoặc điều kiện lọc.'));
  $('#catalog-filter').onsubmit=event=>{event.preventDefault();const f=new FormData(event.target);filters.catalogQ=f.get('q');filters.rarity=f.get('rarity');filters.weapon=f.get('weapon');route();};
  if(user.role==='ADMIN')$('#new-skin').onclick=()=>openSkinForm();
  bindCards(data.items);
}
async function renderInventory(version){
  const data=await api('/inventory');if(version!==renderVersion)return;ownInventory=data.items;tradeUsers=data.users||[];
  const visible=data.items.filter(item=>!filters.inventoryQ||(item.skin_name+' '+item.weapon).toLocaleLowerCase('vi').includes(filters.inventoryQ.toLocaleLowerCase('vi')));
  const unlocked=data.items.filter(item=>!item.locked).length;
  $('#main').innerHTML=header('Kho vật phẩm','Một bộ sưu tập riêng, sẵn sàng cho những lựa chọn tiếp theo.','<button class="primary" id="new-trade">⇄ Tạo đề nghị trao đổi</button>')
    +`<div class="mini-stat-row"><div class="mini-stat"><small>Vật phẩm sở hữu</small><strong>${data.items.length}</strong></div><div class="mini-stat"><small>Sẵn sàng giao dịch</small><strong>${unlocked}</strong></div><div class="mini-stat"><small>Điểm SC của bạn</small><strong>${Number(user.balance).toLocaleString('vi-VN')}</strong></div></div><form class="filterbar" id="inventory-filter"><input name="q" aria-label="Tìm trong kho" placeholder="⌕  Tìm vật phẩm trong kho…" value="${esc(filters.inventoryQ)}"><button type="submit">Tìm kiếm</button><span class="result-count">${visible.length} vật phẩm</span></form>`
    +(visible.length?`<div class="skin-grid">${visible.map((item,index)=>skinCard(item,'inventory',index)).join('')}</div>`:empty('Kho chưa có vật phẩm phù hợp','Khám phá chợ skin hoặc thử một từ khóa khác.'));
  $('#new-trade').onclick=openTrade;
  $('#inventory-filter').onsubmit=event=>{event.preventDefault();filters.inventoryQ=new FormData(event.target).get('q');route();};
  bindCards(data.items);
}
function bindCards(items){
  document.querySelectorAll('[data-skin]').forEach(b=>b.onclick=()=>openDetail(Number(b.dataset.skin)));
  document.querySelectorAll('[data-edit-skin]').forEach(b=>b.onclick=()=>openSkinForm(items.find(i=>i.id===Number(b.dataset.editSkin))));
  document.querySelectorAll('[data-sell]').forEach(b=>b.onclick=()=>openSell(Number(b.dataset.sell)));
  document.querySelectorAll('[data-buy]').forEach(b=>b.onclick=()=>listingAction(b,Number(b.dataset.buy),'buy','Xác nhận mua vật phẩm bằng điểm SC?'));
  document.querySelectorAll('[data-cancel-listing]').forEach(b=>b.onclick=()=>listingAction(b,Number(b.dataset.cancelListing),'cancel','Bạn muốn hủy tin đăng này?'));
  document.querySelectorAll('[data-moderate]').forEach(b=>b.onclick=async()=>{
    const reason=prompt('Nhập lý do ẩn tin đăng:');if(reason===null)return;b.disabled=true;
    try{await api('/listings/'+b.dataset.moderate+'/moderate',{method:'POST',body:{reason}});toast('Đã ẩn tin đăng.');await route();}catch(error){toast(error.message);b.disabled=false;}
  });
}
async function listingAction(button,id,action,question){if(!confirm(question))return;button.disabled=true;try{await api(`/listings/${id}/${action}`,{method:'POST'});await updateWallet();toast(action==='buy'?'Mua vật phẩm thành công.':'Đã hủy tin đăng.');await route();}catch(error){toast(error.message);button.disabled=false;}}
async function openDetail(id){
  try{const {item}=await api('/skins/'+id);$('#skin-detail').innerHTML=`<div class="detail-art ${rarityClass(item.rarity)}">${gunSVG(item.weapon,item.rarity)}</div>${rarityBadge(item.rarity)}<h2 class="detail-skin-name">${esc(item.name)}</h2><dl class="meta-grid"><div class="wide"><dt>TÊN SKIN</dt><dd class="meta-value">${esc(item.name)}</dd></div><div><dt>VŨ KHÍ</dt><dd>${esc(item.weapon)}</dd></div><div><dt>ĐỘ HAO MÒN</dt><dd>${esc(item.wear)}</dd></div><div><dt>FLOAT</dt><dd>${Number(item.float_value).toFixed(6)}</dd></div><div><dt>GIÁ THAM KHẢO</dt><dd class="skin-price">${money(item.reference_price)}</dd></div></dl><p class="help float-help">Float nằm trong khoảng 0 đến 1.</p>`;$('#detail-dialog').showModal();}catch(error){toast(error.message);}
}
function openSell(id){
  const item=ownInventory.find(i=>(i.item_id||i.id)===id);if(!item)return;
  $('#sell-form').reset();$('#sell-error').textContent='';$('#sell-form').elements.item_id.value=id;
  $('#sell-preview').innerHTML=`<div class="preview-item">${gunSVG(item.weapon,item.rarity)}<div><strong>${esc(item.skin_name)}</strong><small>${esc(item.wear)} · Float ${Number(item.float_value).toFixed(4)}</small></div></div>`;
  $('#sell-dialog').showModal();
}
async function openTrade(){
  try{
    const data=await api('/inventory');ownInventory=data.items;tradeUsers=data.users||[];
    const available=data.items.filter(item=>!item.locked);
    if(!available.length){toast('Bạn cần ít nhất một vật phẩm chưa được giữ để trao đổi.');return;}
    $('#trade-form').reset();$('#trade-error').textContent='';
    $('#trade-give').innerHTML=available.map(item=>`<option value="${item.item_id||item.id}">${esc(item.skin_name)} · ${esc(item.wear)}</option>`).join('');
    $('#trade-recipient').innerHTML='<option value="">Chọn thành viên</option>'+tradeUsers.filter(person=>person.id!==user.id).map(person=>`<option value="${person.id}">${esc(person.name)} (${esc(person.username)})</option>`).join('');
    $('#trade-want').innerHTML='<option value="">Chọn thành viên trước</option>';
    $('#trade-dialog').showModal();
  }catch(error){toast(error.message);}
}
$('#trade-recipient').onchange=async event=>{
  const id=event.target.value;$('#trade-want').innerHTML='<option value="">Đang tải…</option>';if(!id){$('#trade-want').innerHTML='<option value="">Chọn thành viên trước</option>';return;}
  try{const data=await api('/inventory?user_id='+id);const free=data.items.filter(i=>!i.locked);$('#trade-want').innerHTML=free.length?'<option value="">Chọn vật phẩm muốn nhận</option>'+free.map(item=>`<option value="${item.item_id||item.id}">${esc(item.skin_name)} · ${esc(item.wear)}</option>`).join(''):'<option value="">Thành viên chưa có vật phẩm sẵn sàng</option>';}catch(error){$('#trade-want').innerHTML='<option value="">Không tải được vật phẩm</option>';toast(error.message);}
};
async function renderTrades(version){
  const {items}=await api('/trades');if(version!==renderVersion)return;
  const visible=items.filter(item=>!filters.tradeStatus||item.status===filters.tradeStatus);
  $('#main').innerHTML=header('Đề nghị trao đổi','Theo dõi đề nghị đã gửi và phản hồi từ những thành viên khác.','<button class="primary" id="new-trade">＋ Tạo đề nghị</button>')
    +`<form class="filterbar" id="trade-filter"><select name="status" aria-label="Trạng thái đề nghị"><option value="">Tất cả trạng thái</option>${['PENDING','ACCEPTED','REJECTED','CANCELLED'].map(s=>`<option value="${s}" ${filters.tradeStatus===s?'selected':''}>${STATUS[s]}</option>`).join('')}</select><button type="submit">Lọc</button><span class="result-count">${visible.length} đề nghị</span></form>`
    +(visible.length?`<div class="trade-list">${visible.map(item=>`<article class="trade-card"><div class="trade-heading"><div><h3>Đề nghị #${item.id} · ${item.proposer_id===user.id?'Bạn gửi':'Bạn nhận'}</h3><p>${esc(item.proposer_name)} → ${esc(item.recipient_name)}</p></div>${badge(item.status)}</div><div class="trade-pair"><div class="trade-item">${gunSVG('AK-47','Restricted')}<div><small>${esc(item.proposer_name)} TRAO</small><strong>${esc(item.give_skin_name)}</strong></div></div><span class="trade-arrow" aria-hidden="true">⇄</span><div class="trade-item">${gunSVG('M4A1-S','Classified')}<div><small>${esc(item.recipient_name)} TRAO</small><strong>${esc(item.want_skin_name)}</strong></div></div></div>${item.status==='PENDING'?`<div class="trade-actions">${item.recipient_id===user.id?`<button class="danger" data-trade-action="reject" data-trade-id="${item.id}">Từ chối</button><button class="primary" data-trade-action="accept" data-trade-id="${item.id}">Chấp nhận trao đổi</button>`:`<button data-trade-action="cancel" data-trade-id="${item.id}">Hủy đề nghị</button>`}</div>`:''}</article>`).join('')}</div>`:empty('Chưa có đề nghị trao đổi','Chọn vật phẩm trong kho để bắt đầu một đề nghị mới.'));
  $('#new-trade').onclick=openTrade;
  $('#trade-filter').onsubmit=event=>{event.preventDefault();filters.tradeStatus=new FormData(event.target).get('status');route();};
  document.querySelectorAll('[data-trade-action]').forEach(button=>button.onclick=async()=>{
    const action=button.dataset.tradeAction;if(!confirm(action==='accept'?'Xác nhận trao đổi quyền sở hữu hai vật phẩm?':'Bạn muốn '+(action==='reject'?'từ chối':'hủy')+' đề nghị này?'))return;button.disabled=true;
    try{await api(`/trades/${button.dataset.tradeId}/action`,{method:'POST',body:{action}});toast('Đã cập nhật đề nghị.');await route();}catch(error){toast(error.message);button.disabled=false;}
  });
}
async function renderHistory(version){
  const {items}=await api('/history');if(version!==renderVersion)return;
  const names={BUY:'Đã mua vật phẩm',SELL:'Đã bán vật phẩm',CREATE_LISTING:'Đăng bán vật phẩm',LIST:'Đăng bán vật phẩm',CANCEL_LISTING:'Hủy tin đăng',CREATE_TRADE:'Tạo đề nghị trao đổi',ACCEPT_TRADE:'Chấp nhận trao đổi',REJECT_TRADE:'Từ chối trao đổi',CANCEL_TRADE:'Hủy đề nghị',MODERATE:'Kiểm duyệt tin đăng',UPDATE_USER:'Cập nhật tài khoản',CREATE_SKIN:'Thêm skin',UPDATE_SKIN:'Cập nhật skin'};
  $('#main').innerHTML=header('Lịch sử giao dịch','Các thay đổi và hoạt động liên quan đến tài khoản của bạn.')+(items.length?`<section class="panel timeline-list">${items.map(item=>`<article class="timeline-row"><span class="timeline-dot">↗</span><div><strong>${esc(names[item.action]||item.action)}</strong><p>${esc(typeof item.detail==='string'?item.detail:JSON.stringify(item.detail))}</p><small>${esc(item.actor_name)} · ${time(item.created_at)} · ${esc(item.entity_type)} #${item.entity_id}</small></div></article>`).join('')}</section>`:empty('Lịch sử còn trống','Các giao dịch và thay đổi của bạn sẽ được lưu tại đây.'));
}
async function renderNotifications(version){
  const {items}=await api('/notifications');if(version!==renderVersion)return;
  $('#main').innerHTML=header('Thông báo','Cập nhật mới nhất về tin đăng và các đề nghị trao đổi.')+(items.length?`<section class="panel">${items.map(item=>`<article class="notification ${item.is_read?'':'unread'}"><div><strong>${esc(item.body)}</strong><p>${esc(item.event_type)}</p><small>${time(item.created_at)} · ${item.is_read?'Đã đọc':'Chưa đọc'}</small></div>${!item.is_read?`<button class="text-button" data-read="${item.id}">Đánh dấu đã đọc</button>`:''}</article>`).join('')}</section>`:empty('Chưa có thông báo','Thông báo về các hoạt động mới sẽ xuất hiện tại đây.'));
  document.querySelectorAll('[data-read]').forEach(button=>button.onclick=async()=>{button.disabled=true;try{await api('/notifications/'+button.dataset.read+'/read',{method:'POST'});await route();}catch(error){toast(error.message);button.disabled=false;}});
}
function openSkinForm(item){
  const form=$('#skin-form');form.reset();$('#skin-error').textContent='';form.elements.id.value=item?.id||'';
  $('#skin-form-title').textContent=item?'Sửa thông tin skin':'Thêm skin';
  if(item){for(const key of ['name','weapon','rarity','wear','float_value','reference_price'])form.elements[key].value=item[key];form.elements.active.checked=!!item.active;}
  $('#skin-dialog').showModal();
}
async function renderUsers(version){
  const {items}=await api('/users');if(version!==renderVersion)return;userItems=items;
  $('#main').innerHTML=header('Quản lý tài khoản','Quản lý vai trò và trạng thái truy cập trong ứng dụng.')+`<section class="panel"><div class="panel-heading"><h3>Tài khoản hệ thống</h3><span class="result-count">${items.length} tài khoản</span></div><div class="table-wrap"><table><thead><tr><th>NGƯỜI DÙNG</th><th>VAI TRÒ</th><th>ĐIỂM SC</th><th>TRẠNG THÁI</th><th></th></tr></thead><tbody>${items.map(person=>`<tr><td><strong class="table-strong">${esc(person.name)}</strong><span class="table-sub">${esc(person.username)}</span></td><td>${ROLE[person.role]}</td><td>${Number(person.balance).toLocaleString('vi-VN')}</td><td>${person.active?'Hoạt động':'Đã khóa'}</td><td><button class="text-button" data-edit-user="${person.id}">Chỉnh sửa ↗</button></td></tr>`).join('')}</tbody></table></div></section>`;
  document.querySelectorAll('[data-edit-user]').forEach(button=>button.onclick=()=>{const person=userItems.find(p=>p.id===Number(button.dataset.editUser));const form=$('#user-form');form.reset();$('#user-error').textContent='';for(const key of ['id','name','role'])form.elements[key].value=person[key];form.elements.active.checked=!!person.active;$('#edit-username').textContent=person.username;$('#user-dialog').showModal();});
}
async function submitForm(event,path,body,dialogId,errorId,method='POST'){
  event.preventDefault();const button=$('button[type=submit]',event.target);button.disabled=true;$(errorId).textContent='';
  try{await api(path,{method,body});$(dialogId).close();toast('Đã lưu thay đổi.');await updateWallet();await route();}catch(error){$(errorId).textContent=error.message;}finally{button.disabled=false;}
}
$('#sell-form').onsubmit=event=>{event.preventDefault();const f=event.target.elements;submitForm(event,'/listings',{item_id:Number(f.item_id.value),price:Number(f.price.value)},'#sell-dialog','#sell-error');};
$('#trade-form').onsubmit=event=>{event.preventDefault();const f=event.target.elements;submitForm(event,'/trades',{give_item_id:Number(f.give_item_id.value),want_item_id:Number(f.want_item_id.value)},'#trade-dialog','#trade-error');};
$('#skin-form').onsubmit=event=>{event.preventDefault();const f=event.target.elements;const id=f.id.value;const body={name:f.name.value,weapon:f.weapon.value,rarity:f.rarity.value,wear:f.wear.value,float_value:Number(f.float_value.value),reference_price:Number(f.reference_price.value),active:f.active.checked};submitForm(event,'/skins'+(id?'/'+id:''),body,'#skin-dialog','#skin-error',id?'PATCH':'POST');};
$('#user-form').onsubmit=event=>{event.preventDefault();const f=event.target.elements;submitForm(event,'/users/'+f.id.value,{name:f.name.value,role:f.role.value,active:f.active.checked},'#user-dialog','#user-error','PATCH');};
document.querySelectorAll('[data-close]').forEach(button=>button.onclick=()=>document.getElementById(button.dataset.close).close());
$('#login-form').onsubmit=async event=>{event.preventDefault();const button=$('button',event.target);button.disabled=true;$('#login-error').textContent='';try{await api('/login',{method:'POST',body:Object.fromEntries(new FormData(event.target))});event.target.reset();await boot();}catch(error){$('#login-error').textContent=error.message;}finally{button.disabled=false;}};
$('#logout').onclick=async()=>{try{await api('/logout',{method:'POST'});location.hash='';showLogin();}catch(error){toast(error.message);}};
window.addEventListener('hashchange',route);
boot().catch(error=>{showLogin();if(error.message!=='Vui lòng đăng nhập.')$('#login-error').textContent=error.message;});
