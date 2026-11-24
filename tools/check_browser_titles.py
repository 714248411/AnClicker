"""Verify numbered native browser titles survive page title and URL changes."""
import os,sys,tempfile,threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.rpa_bridge import RpaBridge
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  body=('<title>'+self.path+'</title><script>document.title="页面自己的标题"</script>').encode('utf8')
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
with tempfile.TemporaryDirectory(prefix='browser-title-',ignore_cleanup_errors=True) as folder:
 os.environ['ANCLICKER_DATA_DIR']=folder
 bridge=RpaBridge('numbered-browser-titles')
 def run(kind,params=None):return bridge.execute({'id':kind,'params':params or {}},timeout=45)['result']
 try:
  for number in range(1,4):
   run('openUrl',{'url':f'http://127.0.0.1:{server.server_port}/{number}','target':'新窗口','waitType':'加载完成'})
   assert run('acInspect')['titles']==['极速网页AC'+str(i) for i in range(1,number+1)]
  before=run('acInspect')
  run('openUrl',{'url':f'http://127.0.0.1:{server.server_port}/changed','target':'当前标签页','waitType':'加载完成'})
  after=run('acInspect')
  assert after['titles']==before['titles']
  assert [p['id'] for p in after['tabs']]==[p['id'] for p in before['tabs']]
  assert all(p['title']=='页面自己的标题' for p in after['tabs']),after
  print('PASS three real browser windows numbered 1/2/3; navigation preserves numbers and original page titles',flush=True)
 finally:bridge.close();server.shutdown();server.server_close()
