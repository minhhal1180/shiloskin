"""Actual API/UI tooling runs, isolated from JMeter process/results and live VPS."""
import json,os,secrets,subprocess,sys,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
from threading import Thread
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import create_app,initialize
from werkzeug.serving import make_server,WSGIRequestHandler
class Quiet(WSGIRequestHandler):
 def log_request(self,*a,**kw):pass
def stamp():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def main():
 out=ROOT/'evidence/tooling';out.mkdir(parents=True,exist_ok=True)
 report={'scope':'Local ShiloSkin API/UI test, isolated temp DB; AI-assisted shared creation, not blind partner assessment','started':stamp(),'runs':{}}
 with tempfile.TemporaryDirectory(prefix='shilo-api-ui-') as tmp:
  app=create_app({'DATABASE':str(Path(tmp)/'shilo.db'),'TRAINING_BUGS':True,'SESSION_COOKIE_SECURE':False,'SECRET_KEY':secrets.token_hex(32)});initialize(app,demo=True)
  server=make_server('127.0.0.1',0,app,threaded=True,request_handler=Quiet);thread=Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}';report['base_url']=base
  try:
   for name,script in [('newman','run-newman.cjs'),('puppeteer','puppeteer.cjs')]:
    start=time.monotonic();started=stamp()
    with (out/f'{name}.log').open('w',encoding='utf-8') as log:run=subprocess.run(['node',script],cwd=ROOT/'tooling',env={**os.environ,'BASE_URL':base},stdout=log,stderr=subprocess.STDOUT)
    report['runs'][name]={'started':started,'finished':stamp(),'wall_seconds':round(time.monotonic()-start,3),'exit_code':run.returncode};print(name,report['runs'][name],flush=True)
  finally:server.shutdown();server.server_close();thread.join(timeout=5)
 report['finished']=stamp();(out/'api-ui-summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 return 0 if all(v['exit_code']==0 for v in report['runs'].values()) else 1
if __name__=='__main__':raise SystemExit(main())
