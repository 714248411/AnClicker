import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.rpa_bridge import RpaBridge
with tempfile.TemporaryDirectory(prefix='ac-remote-bridge-',ignore_cleanup_errors=True) as directory:
 os.environ['ANCLICKER_DATA_DIR']=directory
 bridge=RpaBridge('external-test')
 try:
  def run(kind,params):return bridge.execute({'id':kind,'params':params},timeout=30)['result']
  pages=run('acListCdpWindows',{'cdpEndpoints':[{'endpoint':sys.argv[1],'browser':'测试 Chrome'}]})
  target=next(p for p in pages if p.get('remote') and p['url'].endswith('/one'))
  run('backgroundClick',{'browserWindow':target,'points':'50,40'})
  run('backgroundKey',{'browserWindow':target,'key':'Ctrl+A(全选)'})
  run('backgroundKey',{'browserWindow':target,'key':'自定义','customKey':'z','times':2})
  run('backgroundKey',{'browserWindow':target,'key':'Ctrl+A(全选)'})
  run('backgroundKey',{'browserWindow':target,'key':'自定义','customKey':'aaaaa','interval':.1})
  run('backgroundClicks',{'browserWindow':target,'points':'50,120;50,120','interval':.01})
  print('PASS bridge external target list, keyboard and multiple clicks',flush=True)
 finally:bridge.close()
