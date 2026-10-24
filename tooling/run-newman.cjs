'use strict';
const fs=require('fs'),path=require('path'),newman=require('newman');
const baseUrl=process.env.BASE_URL;if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(baseUrl||''))throw Error('Use tools/run_api_ui.py on isolated data.');
const out=path.resolve(__dirname,'../evidence/tooling/newman');fs.mkdirSync(out,{recursive:true});
const started=new Date().toISOString();
newman.run({collection:require('./shiloskin.postman_collection.json'),environment:{name:'Local isolated ShiloSkin',values:[{key:'baseUrl',value:baseUrl,enabled:true}]},iterationData:path.join(__dirname,'postman-data.csv'),reporters:['cli','htmlextra'],reporter:{htmlextra:{export:path.join(out,'newman-report.html'),title:'ShiloSkin API tests — local AI-assisted build',skipHeaders:true}},timeoutRequest:15000},(error,summary)=>{
 if(error){console.error(error);process.exitCode=1;return;}
 const stats=summary.run.stats;
 const htmlPath=path.join(out,'newman-report.html');
 if(fs.existsSync(htmlPath))fs.writeFileSync(htmlPath,fs.readFileSync(htmlPath,'utf8').replace(/(&quot;csrf&quot;\s*:\s*&quot;)[0-9a-f]+(&quot;)/g,'$1[redacted test nonce]$2'));
 const report={scope:'Actual tests on isolated local ShiloSkin; AI-assisted shared creation, not blind independent testing',started,finished:new Date().toISOString(),baseUrl,iterations:stats.iterations.total,requests:stats.requests.total,assertions:stats.assertions.total,pass:stats.assertions.total-stats.assertions.failed,fail:stats.assertions.failed,requestFailures:stats.requests.failed,failures:summary.run.failures.map(f=>({request:f.source?.name,test:f.error.test||f.error.name,actual:f.error.message})),functionality:['authentication','session/logout','skin catalogue/detail','own and target inventory','market listings','create listing','cancel listing','trade list','history','private notifications','role validation'],redactions:['Ephemeral CSRF nonce in HTML; headers omitted; counts unchanged'],versions:{node:process.version,newman:require('newman/package.json').version,htmlextra:require('newman-reporter-htmlextra/package.json').version}};
 report.scriptErrors=summary.run.failures.filter(f=>f.error.name!=='AssertionError').length;
 fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(report,null,2));console.log('NEWMAN_SUMMARY',JSON.stringify(report));if(report.scriptErrors)process.exitCode=1;
});
