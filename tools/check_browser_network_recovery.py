import os,sys,tempfile,threading,socket
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.rpa_bridge import RpaBridge
from anclicker.domain.instructions import ExecutionContext
class Handler(BaseHTTPRequestHandler):
 count=0
 def do_GET(self):
  if self.path=='/unstable' and Handler.count<2:
   Handler.count+=1
   self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
  body=b'<title>Recovered</title><p id="ready">ok</p>'
  self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
with tempfile.TemporaryDirectory(prefix='ac-network-',ignore_cleanup_errors=True) as folder:
 os.environ['ANCLICKER_DATA_DIR']=folder
 bridge=RpaBridge('network-recovery');logs=[];context=ExecutionContext();context.output=logs.append
 try:
  result=bridge.execute({'id':'openUrl','params':{'url':f'http://127.0.0.1:{server.server_port}/unstable','target':'新窗口','waitType':'加载完成'}},context=context,timeout=60)
  assert Handler.count==2
  assert any('navigation-retry' in str(line) for line in logs),logs
  assert any('ERR_EMPTY_RESPONSE' in p.read_text(encoding='utf-8') for p in Path(folder).rglob('javascript-errors.log'))
  state=bridge.execute({'id':'acInspect','params':{}},timeout=20)['result']
  assert state['tabs'][0]['title']=='Recovered',state
  print('PASS actual browser survives two dropped connections and task continues to inspect',flush=True)
 finally:bridge.close();server.shutdown();server.server_close()
