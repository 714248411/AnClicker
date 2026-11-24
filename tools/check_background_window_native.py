import sys,json,subprocess,os,faulthandler
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
faulthandler.enable()
if '--target' in sys.argv:
 import win32gui,win32con
 wc=win32gui.WNDCLASS();wc.lpszClassName='AnClickerDmWindowRegression'
 def proc(h,m,w,l):
  if m==win32con.WM_CLOSE:win32gui.DestroyWindow(h);return 0
  if m==win32con.WM_DESTROY:win32gui.PostQuitMessage(0);return 0
  return win32gui.DefWindowProc(h,m,w,l)
 wc.lpfnWndProc=proc;win32gui.RegisterClass(wc)
 hwnd=win32gui.CreateWindow(wc.lpszClassName,'DM regression fixture',win32con.WS_OVERLAPPEDWINDOW,10,10,400,240,0,0,0,None)
 print(hwnd,flush=True);win32gui.PumpMessages();raise SystemExit
from anclicker.platform.background_runtime import DmTransport
from anclicker.domain.instructions import ExecutionContext
child=subprocess.Popen([sys.executable,'-u',__file__,'--target'],stdout=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
transport=None
try:
 hwnd=int(child.stdout.readline())
 transport=DmTransport(ExecutionContext())
 print('component',transport.version,flush=True)
 for method,args in [('GetWindowTitle',(hwnd,)),('GetWindowClass',(hwnd,)),('GetWindowProcessId',(hwnd,)),('GetWindowProcessPath',(hwnd,)),('GetWindowRect',(hwnd,)),('GetClientRect',(hwnd,)),('GetClientSize',(hwnd,)),('SetWindowText',(hwnd,'DM regression renamed')),('SetWindowSize',(hwnd,450,260)),('SetClientSize',(hwnd,300,200)),('MoveWindow',(hwnd,30,40)),('GetWindowState',(hwnd,0))]:
  from anclicker.platform.background_catalog import METHODS, values_for
  inputs=[item for item in METHODS[method]['args'] if not item['out'] or item.get('inout')]
  arguments=values_for(method,{item['name']:value for item,value in zip(inputs,args)})
  print(method,transport.call(method,*arguments,raw=True),flush=True)
 print('PASS native window getter/setter calls on isolated fixture',flush=True)
finally:
 if transport:transport.close()
 child.terminate();child.wait(timeout=5)
