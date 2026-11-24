import sys,ctypes
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ctypes import wintypes
from anclicker.platform.qt_compat.QtCore import Qt,QTimer,QEventLoop
from anclicker.platform.qt_compat.QtWidgets import QApplication,QDialog,QDockWidget,QWidget,QVBoxLayout,QLabel
from anclicker.ui.window_chrome import FramelessMainWindow
from anclicker.ui.window_edges import apply_window_edges
from anclicker.ui.information_dialogs import InformationDialog
app=QApplication([])
def pump():
 loop=QEventLoop();QTimer.singleShot(80,loop.quit);loop.exec_()
w=FramelessMainWindow();w.view_workspace=SimpleNamespace(theme_mode='light');w.resize(600,400);w.show();pump()
d=InformationDialog(w);d.resize(420,260);d.show();pump()
plain=QDialog(w);plain.resize(300,200);plain.show();pump()
dock=QDockWidget('设置',w);dock.setWidget(QWidget());w.addDockWidget(Qt.RightDockWidgetArea,dock);dock.setFloating(True);dock.show();pump()
get=ctypes.windll.dwmapi.DwmGetWindowAttribute
get.argtypes=[wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
def attribute(window,key):
 value=ctypes.c_int();result=get(int(window.winId()),key,ctypes.byref(value),ctypes.sizeof(value));return result,value.value
for mode in ('light','dark'):
 w.view_workspace.theme_mode=mode
 for window in (w,d,plain,dock):
  before=window.geometry();apply_window_edges(window);pump()
  assert window.geometry()==before
  shadow=window._outer_shadow
  assert shadow.isVisible() and shadow.testAttribute(Qt.WA_TransparentForMouseEvents)
  assert shadow.windowFlags() & Qt.WindowTransparentForInput
  assert shadow.geometry()==window.frameGeometry().adjusted(-22,-22,22,22)
  assert window._edge_signature[1]==(mode=='dark')
  result,value=attribute(window,20)
  if result==0:assert value==int(mode=='dark')
  result,value=attribute(window,33)
  if result==0:assert value==2
w.showMaximized();pump();assert w._edge_signature[2] and not w._outer_shadow.isVisible()
w.showNormal();pump();assert not w._edge_signature[2]
dock.setFloating(False);pump();assert not dock._outer_shadow.isVisible()
plain.hide();pump();assert not plain._outer_shadow.isVisible()
picker=QDialog(w);picker.setWindowFlags(Qt.Tool|Qt.FramelessWindowHint);picker.show();pump();assert not hasattr(picker,'_edge_signature')
for i in range(20):
 temp=QDialog(w);temp.setAttribute(Qt.WA_DeleteOnClose);temp.show();temp.close()
pump()
for window in (picker,dock,plain,d,w):window.close()
pump();print('PASS native DWM light/dark attributes, main/settings/floating windows, unchanged geometry, maximize/restore, picker exclusions and rapid close')
