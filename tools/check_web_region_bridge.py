import sys,threading
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from anclicker.platform.rpa_bridge import RpaBridge
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write('<html><body style="margin:0"><div style="position:absolute;left:30px;top:30px">区域管道测试</div></body></html>'.encode())
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
bridge=RpaBridge('region-regression')
try:
 bridge.execute({'id':'openUrl','params':{'url':'http://127.0.0.1:'+str(server.server_port),'engine':'跟随当前','target':'新窗口','loginMode':'独立登录(每次全新)','waitType':'加载完成'}})
 region=bridge.execute({'id':'acRegion','params':{'action':'geometry'}})['result'];region.update(x=0,y=0,w=300,h=150)
 result=bridge.execute({'id':'acRegion','params':{'action':'extract','region':region,'maxChars':20000}})['result']
 assert '区域管道测试' in result['text'],result
 print('PASS browser bridge IPC region extraction')
finally:bridge.close();server.shutdown()
