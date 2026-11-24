import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtCore import Qt,QPoint,QPointF,QEvent,QEventLoop,QTimer
from anclicker.platform.qt_compat.QtGui import QMouseEvent
from anclicker.platform.qt_compat.QtWidgets import QApplication,QDialog
from anclicker.ui.window_chrome import FramelessMainWindow
from anclicker.ui.window_edges import apply_window_edges
app=QApplication([])
def pump():
 loop=QEventLoop();QTimer.singleShot(50,loop.quit);loop.exec_()
def drag(grip,delta):
 local=QPoint(18 if grip.right else 3,18 if grip.bottom else 3)
 origin=grip.mapToGlobal(local)
 for kind,global_point,button,buttons in ((QEvent.MouseButtonPress,origin,Qt.LeftButton,Qt.LeftButton),(QEvent.MouseMove,origin+delta,Qt.NoButton,Qt.LeftButton),(QEvent.MouseButtonRelease,origin+delta,Qt.LeftButton,Qt.NoButton)):
  event=QMouseEvent(kind,QPointF(grip.mapFromGlobal(global_point)),QPointF(global_point),button,buttons,Qt.NoModifier)
  QApplication.sendEvent(grip,event)
 pump()
w=FramelessMainWindow();w.resize(600,400);w.move(150,150);w.show();pump()
d=QDialog(w);d.resize(400,300);d.show();pump()
for window in (w,d):
 apply_window_edges(window)
 for grip in window._corner_grips:
  assert grip.isVisible()
  assert grip.mask().contains(QPoint(18 if grip.right else 3,18 if grip.bottom else 3))
  assert not grip.mask().contains(QPoint(4 if grip.right else 17,4 if grip.bottom else 17))
  before=window.geometry()
  drag(grip,QPoint(24 if grip.right else -24,20 if grip.bottom else -20))
  assert window.width()==before.width()+24 and window.height()==before.height()+20,(before,window.geometry())
  window.setGeometry(before);pump()
w.showMaximized();pump();assert all(not g.isVisible() for g in w._corner_grips)
w.showNormal();pump();assert all(g.isVisible() for g in w._corner_grips)
d.setFixedSize(d.size());apply_window_edges(d);assert all(not g.isVisible() for g in d._corner_grips)
d.close();w.close();pump()
print('PASS actual diagonal resize at all four corners on main/dialog, L-shaped targets, content exclusions, maximize/restore and fixed-size guard')
