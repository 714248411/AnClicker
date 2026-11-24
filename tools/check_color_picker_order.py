import sys,os,importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));os.environ['QT_QPA_PLATFORM']='windows'
from PIL import Image
from anclicker.platform.qt_compat import BINDING
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtCore import Qt,QPointF
from anclicker.ui.instruction_editors.glyph_color_picker import GlyphColorPicker
from anclicker.platform.vision_tools.glyph_colors import normalize_priorities,priority_groups
QTest=importlib.import_module(BINDING+'.QtTest').QTest
app=QApplication([]);image=Image.new('RGB',(200,100),'white')
for x,color in [(20,(255,0,0)),(60,(0,0,255)),(100,(255,255,0)),(140,(192,40,21))]:image.putpixel((x,30),color)
d=GlyphColorPicker(image);d.show();app.processEvents();c=d.canvas
for x in (20,60,100,140):QTest.mouseClick(c,Qt.LeftButton,Qt.NoModifier,c.marker_position((x,30)).toPoint())
assert len(d.samples)==4 and [r['point'][0] for r in d.samples]==[20,60,100,140]
assert d.order.text()=='红色;蓝色;黄色;192,40,21',d.order.text()
QTest.mouseClick(c,Qt.RightButton,Qt.NoModifier,c.marker_position((60,30)).toPoint());assert [r['point'][0] for r in d.samples]==[20,100,140]
QTest.keyClick(c,Qt.Key_Z,Qt.ControlModifier);assert [r['point'][0] for r in d.samples]==[20,60,100,140]
QTest.keyClick(c,Qt.Key_Right);assert d.samples[-1]['point']==(141,30)
QTest.keyClick(c,Qt.Key_Z,Qt.ControlModifier);assert d.samples[-1]['point']==(140,30)
d.clear();assert not d.samples;d.undo();assert len(d.samples)==4
# Dragging is neither pickup nor deletion.
class E:
 def __init__(self,p,b):self.p=p;self.b=b
 def position(self):return self.p
 def button(self):return self.b
 def accept(self):pass
for button in (Qt.LeftButton,Qt.RightButton):
 start=c.marker_position((20,30));c.mousePressEvent(E(start,button));c.mouseMoveEvent(E(start+QPointF(50,10),button));c.mouseReleaseEvent(E(start+QPointF(50,10),button));assert len(d.samples)==4
point=QPointF(100,100);before=c.client_point(point,True);c.zoom_at(point,1.2);assert c.client_point(point,True)==before
assert normalize_priorities('红色；蓝色，黄色；192，40，21')=='红色;蓝色;黄色;192,40,21'
assert priority_groups('红色;蓝色;192,40,21',[])==[[(255,0,0)],[(0,0,255)],[(192,40,21)]]
c.fit();app.processEvents();out=Path('artifacts/validation/glyph-capture');out.mkdir(parents=True,exist_ok=True);d.grab().save(str(out/'color-order.png'));d.close()
print('PASS continuous picks, numbered creation order, right-click targeted deletion, Ctrl+Z restores deletion/movement/clear, drag no pick/delete, zoom coordinates, Chinese punctuation and RGB order')
