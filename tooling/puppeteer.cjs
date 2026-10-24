'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),puppeteer=require('puppeteer-core');
const data=require('./ui-data.json'),base=process.env.BASE_URL;
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(base||''))throw Error('Use isolated tools/run_api_ui.py.');
const out=path.resolve(__dirname,'../evidence/tooling/puppeteer');fs.mkdirSync(out,{recursive:true});
const checks=[],flows=[],errors=[];
async function check(name,fn){try{await fn();checks.push({name,result:'Pass'});}catch(error){checks.push({name,result:'Fail',actual:error.message});}}
async function login(browser,credentials){const context=await browser.createBrowserContext();const page=await context.newPage();await page.setViewport({width:1366,height:900});page.setDefaultTimeout(20000);page.on('pageerror',e=>errors.push(e.message));await page.goto(base,{waitUntil:'networkidle0'});await page.type('#login-form [name=username]',credentials.username);await page.type('#login-form [name=password]',credentials.password);await page.click('#login-form button[type=submit]');await page.waitForSelector('#workspace:not([hidden])');await page.waitForSelector('#main h1');return page;}
async function json(page,url){return page.evaluate(async path=>(await(await fetch(path)).json()),url);}
(async()=>{
 const started=new Date().toISOString();const browser=await puppeteer.launch({executablePath:process.env.BROWSER_EXECUTABLE||'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',headless:true});
 try{
  const member=await login(browser,data.member),other=await login(browser,data.other);
  await check('FLOW-01 / member role',async()=>assert.equal((await json(member,'/api/me')).user.role,'MEMBER'));
  await check('FLOW-01 / listing prices use fictional SC',async()=>assert.equal(await member.$eval('.skin-price .currency-text',e=>e.textContent),'SC'));
  await member.screenshot({path:path.join(out,'flow01-01-market.png'),fullPage:true});
  member.once('dialog',dialog=>dialog.accept());await member.click(`[data-buy="${data.purchase.listing_id}"]`);
  await member.waitForFunction(balance=>document.querySelector('#balance')?.textContent===String(balance),{},data.purchase.expected_balance);
  await check('FLOW-01 / buyer balance decreased once',async()=>assert.equal((await json(member,'/api/me')).user.balance,data.purchase.expected_balance));
  await check('FLOW-01 / sold listing leaves active market',async()=>assert.equal((await json(member,'/api/listings?status=ACTIVE')).items.some(i=>i.id===data.purchase.listing_id),false));
  await member.click('[data-nav=inventory]');await member.waitForSelector('[data-sell]');
  await check('FLOW-01 / bought item belongs to buyer',async()=>assert.equal((await json(member,'/api/inventory')).items.find(i=>i.id===data.purchase.item_id).owner_id,data.member.id));
  await member.screenshot({path:path.join(out,'flow01-02-purchased.png'),fullPage:true});
  flows.push({id:'FLOW-01',name:'Browse → buy listing → verify balance/ownership',steps:5,result:checks.some(c=>c.name.startsWith('FLOW-01')&&c.result==='Fail')?'Fail':'Pass',screenshots:['flow01-01-market.png','flow01-02-purchased.png']});
  await member.click('#new-trade');await member.select('#trade-give',String(data.trade.give_item_id));await member.select('#trade-recipient',String(data.trade.recipient_id));await member.waitForSelector(`#trade-want option[value="${data.trade.want_item_id}"]`);await member.select('#trade-want',String(data.trade.want_item_id));await member.click('#trade-form button[type=submit]');await member.waitForSelector('#trade-dialog:not([open])');
  const pending=(await json(member,'/api/trades')).items.find(t=>t.give_item_id===data.trade.give_item_id&&t.want_item_id===data.trade.want_item_id);
  await check('FLOW-02 / proposal enters PENDING',async()=>assert.equal(pending.status,'PENDING'));
  await other.click('[data-nav=trades]');await other.waitForSelector(`[data-trade-id="${pending.id}"][data-trade-action=accept]`);other.once('dialog',dialog=>dialog.accept());
  await Promise.all([other.waitForResponse(r=>r.url().endsWith(`/trades/${pending.id}/action`)&&r.request().method()==='POST'),other.click(`[data-trade-id="${pending.id}"][data-trade-action=accept]`)]);
  await other.waitForFunction(()=>document.querySelector('.trade-card')&&!document.querySelector('[data-trade-action=accept]'));
  await check('FLOW-02 / backend ACCEPTED',async()=>assert.equal((await json(other,'/api/trades')).items.find(t=>t.id===pending.id).status,'ACCEPTED'));
  await check('FLOW-02 / accepted label matches state',async()=>assert.equal(await other.$eval('.trade-card .status-badge',e=>e.textContent),'Đã chấp nhận'));
  await check('FLOW-02 / both item owners swap atomically',async()=>{const a=(await json(member,'/api/inventory')).items,b=(await json(other,'/api/inventory')).items;assert.equal(a.find(i=>i.id===data.trade.want_item_id).owner_id,data.member.id);assert.equal(b.find(i=>i.id===data.trade.give_item_id).owner_id,data.other.id);});
  await other.screenshot({path:path.join(out,'flow02-accepted-trade.png'),fullPage:true});
  flows.push({id:'FLOW-02',name:'Create proposal → recipient accepts → verify ownership',steps:7,result:checks.some(c=>c.name.startsWith('FLOW-02')&&c.result==='Fail')?'Fail':'Pass',screenshots:['flow02-accepted-trade.png']});
  await check('No JavaScript page errors',async()=>assert.deepEqual(errors,[]));
 }catch(error){checks.push({name:'Tool/runtime exception',result:'Blocked',actual:error.stack});}
 finally{const report={scope:'Actual UI tests on isolated local ShiloSkin; AI-assisted shared creation, not blind independent testing',started,finished:new Date().toISOString(),base_url:base,versions:{node:process.version,puppeteer:require('puppeteer-core/package.json').version,browser:await browser.version()},flows,checks,assertions:checks.length,pass:checks.filter(c=>c.result==='Pass').length,fail:checks.filter(c=>c.result==='Fail').length,blocked:checks.filter(c=>c.result==='Blocked').length,errors};fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(report,null,2));console.log('PUPPETEER_SUMMARY',JSON.stringify(report));await browser.close();if(report.blocked)process.exitCode=1;}
})();
