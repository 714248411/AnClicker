import os,sys,tempfile,threading,time,json
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from anclicker.platform.rpa_bridge import RpaBridge
HTML='''<!doctype html><meta charset="utf-8"><style>body{margin:0;height:5000px}#target{position:absolute;top:2400px;left:45%;height:40px}#box{position:absolute;top:3400px;left:30%;width:400px;height:250px;overflow:auto}#inside{position:relative;height:2000px}#nested{position:absolute;top:1000px;height:30px}iframe{position:absolute;top:4200px;height:300px;width:600px}#hidden{display:none}</style><button id="target" onclick="this.textContent='错误点击'">目标按钮</button><button id="edge" style="position:absolute;top:4960px;height:40px">页尾</button><div id="shadow" style="position:absolute;top:1800px"></div><div id="box"><div id="inside"><button id="nested">内部目标</button></div></div><div id="hidden">隐藏目标</div><iframe src="/frame"></iframe><script>document.querySelector('#shadow').attachShadow({mode:'open'}).innerHTML='<button id=shadowTarget>影子目标</button>';setTimeout(()=>{const e=document.createElement('button');e.id='late';e.style='position:absolute;top:2000px';e.textContent='延迟目标';document.body.append(e)},500)</script>'''
FRAME='''<style>body{height:2400px}button{position:absolute;top:1200px}</style><button id="frameTarget">框架目标</button>'''
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  b=(FRAME if self.path.startswith('/frame') else HTML).encode();self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.end_headers();self.wfile.write(b)
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
bridge=RpaBridge('scroll-center-check')
with tempfile.TemporaryDirectory(prefix='ac-scroll-',ignore_cleanup_errors=True) as data:
 os.environ['ANCLICKER_DATA_DIR']=data
 try:
  def run(kind,params):return bridge.execute({'id':kind,'params':params},timeout=35)['result']
  run('openUrl',{'url':f'http://127.0.0.1:{server.server_port}','target':'新窗口','waitType':'加载完成'})
  for by,selector,behavior in [('CSS选择器','#target','平滑滚动'),('XPath','//*[@id="target"]','立即定位'),('文本内容','目标按钮','平滑滚动'),('CSS选择器','#nested','平滑滚动'),('CSS选择器','#frameTarget','立即定位'),('CSS选择器','#late','立即定位'),('CSS选择器','#shadowTarget','平滑滚动')]:
   r=run('scrollElementToCenter',{'selector':selector,'by':by,'behavior':behavior,'settle':0})['rect']
   assert abs(r['y']+r['height']/2-r['viewportHeight']/2)<3,(selector,r)
   print('PASS centered',by,selector,behavior,flush=True)
  r=run('scrollElementToCenter',{'selector':'#edge','by':'CSS选择器','settle':0})['rect']
  assert r['y']>=0 and r['y']+r['height']<=r['viewportHeight']+2,r
  print('PASS page boundary stays visible without overscrolling',flush=True)
  for selector in ['#missing','#hidden']:
   start=time.monotonic()
   try:run('scrollElementToCenter',{'selector':selector,'by':'CSS选择器','timeout':.3})
   except RuntimeError as e:assert '超时' in str(e),e
   else:raise AssertionError(selector)
   assert time.monotonic()-start<6
  print('PASS hidden/missing element timeout',flush=True)
 finally:bridge.close();server.shutdown();server.server_close()
print('PASS real browser scroll regression',flush=True)
