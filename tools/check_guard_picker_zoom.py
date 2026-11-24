import os,sys,importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));os.environ['QT_QPA_PLATFORM']='windows'
from PIL import Image
from anclicker.platform.qt_compat import BINDING
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtCore import Qt,QPointF,QPoint
from anclicker.platform.qt_compat.QtGui import QWheelEvent
from anclicker.ui.instruction_editors.guard_color_picker import GuardColorPicker
QTest=importlib.import_module(BINDING+'.QtTest').QTest
app=QApplication([]);frame=Image.new('RGB',(200,100),'white');frame.putpixel((60,30),(192,40,21))
d=GuardColorPicker(frame);d.setAttribute(Qt.WA_DontShowOnScreen,True);d.show();app.processEvents();c=d.canvas
point=c.marker_position((60,30));before=c.client_point(point)
wheel=QWheelEvent(point,c.mapToGlobal(point.toPoint()),QPoint(),QPoint(0,120),Qt.NoButton,Qt.NoModifier,Qt.NoScrollPhase,False)
QApplication.sendEvent(c,wheel);assert c.zoom>1 and c.client_point(point)==before
QTest.mouseClick(c,Qt.LeftButton,Qt.NoModifier,c.marker_position((60,30)).toPoint())
assert c.result().point==(60,30) and c.result().color==(192,40,21)
class E:
 def __init__(self,p):self.p=p
 def position(self):return self.p
 def button(self):return Qt.LeftButton
 def accept(self):pass
start=c.marker_position((60,30));c.mousePressEvent(E(start));c.mouseMoveEvent(E(start+QPointF(80,20)));c.mouseReleaseEvent(E(start+QPointF(80,20)))
assert c.result().point==(60,30)
QTest.mouseClick(c,Qt.LeftButton,Qt.NoModifier,c.marker_position((60,30)).toPoint());assert c.result().color==(192,40,21)
QTest.keyClick(c,Qt.Key_Right);assert c.result().point==(61,30)
QTest.keyClick(c,Qt.Key_Left);assert c.result().color==(192,40,21)
c.zoom_at(c.marker_position((60,30)),1/1.2);assert abs(c.zoom-1)<1e-9
c.fit();assert c.pan==QPointF()
d.close();print('PASS wheel zoom, anchored coordinates, pan without picking, original RGB, arrow micro-adjustment, zoom out and fit')
