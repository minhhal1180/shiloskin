'use strict';
// Screenshots of Apache's generated dashboard; no reconstructed or invented plots.
const fs=require('fs');
const path=require('path');
const http=require('http');
const puppeteer=require('puppeteer-core');
const root=path.resolve(__dirname,'../evidence/tooling');
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.woff2':'font/woff2','.woff':'font/woff','.svg':'image/svg+xml'};
const server=http.createServer((request,response)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(new URL(request.url,'http://localhost').pathname));
  if(!file.startsWith(root+path.sep)){response.writeHead(403).end();return;}
  fs.readFile(file,(error,body)=>{if(error){response.writeHead(404).end();return;}response.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');response.end(body);});
});
server.listen(0,'127.0.0.1',async()=>{
  let browser;
  const captured=[];
  try{
    browser=await puppeteer.launch({executablePath:process.env.BROWSER_EXECUTABLE||'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',headless:true});
    const page=await browser.newPage();
    await page.setViewport({width:1500,height:1000});
    for(const directory of fs.readdirSync(root).filter(name=>name.startsWith('jmeter-'))){
      const dashboard=path.join(root,directory,'dashboard');
      if(!fs.existsSync(path.join(dashboard,'index.html')))continue;
      const base=`http://127.0.0.1:${server.address().port}/${directory}/dashboard`;
      await page.goto(base+'/index.html',{waitUntil:'networkidle0'});
      await page.screenshot({path:path.join(root,directory,'dashboard-overview.png'),fullPage:true});
      await page.goto(base+'/content/pages/OverTime.html',{waitUntil:'networkidle0'});
      await page.waitForSelector('#responseTimesOverTime canvas');
      await (await page.$('#responseTimesOverTime')).screenshot({path:path.join(root,directory,'response-times-over-time.png')});
      await page.click('#activeThreadsOverTime .click-title');
      await page.waitForFunction(()=>document.querySelector('#bodyActiveThreadsOverTime')?.classList.contains('in'));
      await page.waitForSelector('#activeThreadsOverTime canvas');
      await new Promise(resolve=>setTimeout(resolve,500));
      await (await page.$('#activeThreadsOverTime')).screenshot({path:path.join(root,directory,'active-threads-over-time.png')});
      await page.goto(base+'/content/pages/Throughput.html',{waitUntil:'networkidle0'});
      await page.waitForSelector('#hitsPerSecond canvas');
      await (await page.$('#hitsPerSecond')).screenshot({path:path.join(root,directory,'throughput-over-time.png')});
      captured.push(directory);
    }
    console.log('Captured native Apache dashboard screenshots:',captured.join(', '));
  }catch(error){console.error(error);process.exitCode=1;}
  finally{if(browser)await browser.close();server.close();}
});
