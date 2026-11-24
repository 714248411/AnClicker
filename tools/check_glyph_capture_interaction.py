import os,sys,importlib,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));os.environ['QT_QPA_PLATFORM']='windows'
from PIL import Image
from anclicker.platform.qt_compat import BINDING
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtGui import QFont
from anclicker.platform.qt_compat.QtCore import Qt,QRect,QPointF
from anclicker.ui.instruction_editors.glyph_capture import GlyphCaptureDialog
from anclicker.ui.settings_theme import apply_settings_theme
QTest=importlib.import_module(BINDING+'.QtTest').QTest
app=QApplication([]);app.setFont(QFont('Microsoft YaHei',10))
image=Image.new('RGB',(1200,800),'#dddddd');dialog=GlyphCaptureDialog(image);apply_settings_theme(dialog,None);dialog.show();app.processEvents();c=dialog.canvas
# Zoom anchored at cursor preserves the selected image pixel.
pos=QPointF(c.width()*.4,c.height()*.4);before=c.client_point(pos);c.zoom_at(pos,2.4);after=c.client_point(pos);assert all(abs(x-y)<=1 for x,y in zip(before,after))
c.selection=QRect(100,100,120,40);c.point=(160,120);c.setFocus();QTest.keyClick(c,Qt.Key_Right);QTest.keyClick(c,Qt.Key_Down,Qt.ShiftModifier)
assert c.selection==QRect(101,110,120,40)
# Exercise view drag and selected-box drag in source coordinates.
class Event:
    def __init__(self,p,button=Qt.LeftButton):self.p=p;self.b=button
    def position(self):return self.p
    def button(self):return self.b
    def accept(self):pass
c.fit();r=c.selection_rect();start=r.center();c.mousePressEvent(Event(start));c.mouseMoveEvent(Event(start+QPointF(20,10)));c.mouseReleaseEvent(Event(start+QPointF(20,10)))
assert c.selection.x()>101 and c.selection.size()==QRect(101,110,120,40).size()
selected=QRect(c.selection);old_pan=QPointF(c.pan);c.mousePressEvent(Event(start,Qt.RightButton));c.mouseMoveEvent(Event(start+QPointF(40,30),Qt.RightButton));c.mouseReleaseEvent(Event(start+QPointF(40,30),Qt.RightButton))
assert c.pan==old_pan+QPointF(40,30) and c.selection==selected
c.selection=QRect(1190,790,10,10);c.point=(1195,795);c.fit();c.setFocus();QTest.keyClick(c,Qt.Key_Return);app.processEvents()
assert dialog.entryPanel.isVisible() and c.rect().contains(dialog.entryPanel.geometry())
QTest.keyClick(dialog.textEdit,Qt.Key_Escape);app.processEvents();assert not dialog.entryPanel.isVisible()
# Constrain all four image corners and an offscreen zoomed selection.
for x,y in [(0,0),(1190,0),(0,790),(1190,790)]:
    c.selection=QRect(x,y,10,10);c.point=(x,y);dialog.show_entry();app.processEvents();assert c.rect().contains(dialog.entryPanel.geometry())
c.zoom_at(QPointF(0,0),8);dialog.place_entry();assert c.rect().contains(dialog.entryPanel.geometry())
output=Path('artifacts/validation/glyph-capture');output.mkdir(parents=True,exist_ok=True)
c.fit();c.selection=QRect(450,300,240,50);c.point=(570,325);dialog.show_entry();dialog.textEdit.setText('灯笼');app.processEvents();dialog.grab().save(str(output/'inline-text.png'))
QTest.keyClick(dialog.textEdit,Qt.Key_Return);assert dialog.result()==dialog.Accepted
result=c.result();assert result.region==(450,300,240,50) and result.image.size==(240,50)
print('PASS cursor-anchored zoom, image pan, selected-box drag, image-pixel arrows, inline Enter text, Escape adjustment, edge clamping, lossless selection')
