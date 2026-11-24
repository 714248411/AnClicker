"""Live bundled-browser CDP input and persisted-session regression."""
import os, sys, tempfile, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.rpa_bridge import RpaBridge
from anclicker.instructions.registry import iter_instruction_specs
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.domain.instructions import InstructionDraft
import win32gui, win32con

HTML = b'''<title>CDP Test</title><style>body{margin:0}input{position:absolute;left:20px;top:20px;width:200px;height:40px}button{position:absolute;left:20px;top:100px;width:200px;height:40px}</style>
<a href="/popup" target="_blank" style="position:absolute;left:300px;top:100px;width:100px;height:50px">popup</a><input id="field"><button id="button">click</button><pre id="out" style="position:absolute;top:160px"></pre><pre id="saved" style="position:absolute;top:220px"></pre>
<script>let n=0;document.querySelector('#button').onclick=e=>{document.querySelector('#out').textContent=(++n)+':'+e.isTrusted;localStorage.setItem('test','kept');document.cookie='test=kept;max-age=3600;path=/'};document.querySelector('#saved').textContent=localStorage.getItem('test')+'|'+document.cookie;</script>'''
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(HTML)
 def log_message(self,*_):pass

def main():
 app=QApplication.instance() or QApplication([])
 with patch('anclicker.ui.instruction_editors.background_web.BackgroundWebEditor.refresh_windows'):
  for spec in iter_instruction_specs('网页后台操作'):
   e=spec.create_editor();assert e.open_button.text()=='打开网页';assert e.refresh_button.text()=='刷新窗口'
   if 'points' in e._controls:
    e._controls['points'].setText('50,40');assert e.get_draft().parameters['points']=='50,40'
   else: assert e.get_draft().parameters['key']=='回车(Enter)'
   e.close()
 print('PASS three registered editors and settings',flush=True)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 with tempfile.TemporaryDirectory(prefix='ac-cdp-',ignore_cleanup_errors=True) as folder:
  os.environ['ANCLICKER_DATA_DIR']=folder
  bridge=RpaBridge('cdp-test')
  def run(kind,p=None):return bridge.execute({'id':kind,'params':p or {}},timeout=45)['result']
  def text(page,selector):return bridge.execute({'id':'getText','params':{'browserWindow':page,'selector':selector,'by':'CSS选择器','varName':'text'}},timeout=45)['variables']['text']
  try:
   pages=run('acOpenCdpPage',{'url':f'http://127.0.0.1:{server.server_port}/one'});one=pages[-1]
   pages=run('acOpenCdpPage',{'url':f'http://127.0.0.1:{server.server_port}/two'});two=pages[-1]
   assert one['cdpKey'] != two['cdpKey']
   hwnd=win32gui.GetForegroundWindow()
   run('backgroundClick',{'browserWindow':one,'points':'50,120'})
   assert win32gui.GetForegroundWindow()==hwnd,'background click stole focus'
   run('backgroundClick',{'browserWindow':one,'points':'50,40'})
   run('backgroundKey',{'browserWindow':one,'key':'自定义','customKey':'a','times':2})
   assert win32gui.GetForegroundWindow()==hwnd,'background key stole focus'
   assert text(one,'#out')=='1:true'
   assert text(one,'#field')=='aa'
   run('backgroundKey',{'browserWindow':one,'key':'Ctrl+A(全选)'})
   run('backgroundKey',{'browserWindow':one,'key':'自定义','customKey':'7'})
   assert text(one,'#field')=='7'
   assert text(two,'#field') in ('',None,False),repr(text(two,'#field'))
   run('backgroundClicks',{'browserWindow':one,'points':'50,120;50,120','interval':0.01})
   assert text(one,'#out')=='3:true'
   print('PASS trusted CDP clicks, keys, Ctrl+A, repeated points; no foreground switch; independent pages',flush=True)
   # Minimized target must not restore or steal focus.
   text(one,'#field'); target=win32gui.GetForegroundWindow();win32gui.ShowWindow(target,win32con.SW_MINIMIZE)
   time.sleep(0.4);foreground=win32gui.GetForegroundWindow()
   run('backgroundClick',{'browserWindow':one,'points':'50,120'})
   assert win32gui.IsIconic(target) and win32gui.GetForegroundWindow()!=target,(target,win32gui.IsIconic(target),foreground,win32gui.GetForegroundWindow())
   print('PASS minimized background click',flush=True)
   for params in ({'browserWindow':one,'points':'99999,99999'},{'browserWindow':dict(one,id='gone',cdpKey='gone',url='http://missing.invalid'),'points':'50,120'}):
    try:run('backgroundClick',params)
    except RuntimeError:pass
    else:raise AssertionError('invalid target or out-of-view coordinate accepted')
   run('backgroundClick',{'browserWindow':one,'points':'320,110'})
   time.sleep(.3)
   available=run('acListCdpWindows')
   popup=next(p for p in available if p['url'].endswith('/popup'))
   assert len(available)==2,available  # Existing browser policy opens target=_blank in the same window.
   assert text(popup,'#saved')=='kept|test=kept'
   run('backgroundClick',{'browserWindow':popup,'points':'50,120'})
   assert text(popup,'#out')=='1:true'
   print('PASS refreshed navigation target remains listed and operable',flush=True)
   bridge.close()
   pages=run('acListCdpWindows');assert len(pages)==2,pages
   assert {p['cdpKey'] for p in pages}=={one['cdpKey'],two['cdpKey']}
   # Saved command with old runtime id resolves by persistent identity.
   run('backgroundClick',{'browserWindow':one,'points':'50,40'})
   run('backgroundKey',{'browserWindow':one,'key':'自定义','customKey':'b'})
   assert text(one,'#field')=='b',repr(text(one,'#field'))
   assert text(one,'#saved')=='kept|test=kept',text(one,'#saved')
   assert text(two,'#saved')=='null|',text(two,'#saved')
   assert len(run('acListCdpWindows'))==2
   print('PASS restart restores URLs, stable identity, isolated cookies/localStorage; no duplicate windows',flush=True)
  finally:bridge.close();server.shutdown();server.server_close()
 return 0
if __name__=='__main__':raise SystemExit(main())
