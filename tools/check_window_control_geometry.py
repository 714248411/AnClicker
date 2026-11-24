import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication, QWidget
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.instruction_editors.其他.窗口控制 import InstructionEditor
from anclicker.instructions.其他.窗口控制.executor import adjust_geometry
app=QApplication.instance() or QApplication([])
e=InstructionEditor(draft=InstructionDraft('窗口控制',{'标题包含':'fixture','操作':'窗口移动','移动方式':'相对当前位置','X':-20,'Y':30}))
assert e.get_draft().parameters['X']==-20
assert not e._controls['X'].isHidden() and e._controls['宽度'].isHidden()
e._controls['操作'].setCurrentText('窗口大小')
assert e._controls['X'].isHidden() and not e._controls['宽度'].isHidden()
e._controls['大小锚点'].setCurrentText('中心点')
assert e.get_draft().parameters['大小锚点']=='中心点'
e._controls['操作'].setCurrentText('激活')
assert all(e._controls[k].isHidden() for k in ('X','Y','宽度','高度','大小锚点'))
e.close()
print('PASS parameter switching, old operation compatibility and saved draft')
class Window:
 isMinimized=False;isMaximized=False
 left=100;top=200;width=800;height=600
 def moveTo(self,x,y):self.left=x;self.top=y
 def resizeTo(self,w,h):self.width=w;self.height=h
 def restore(self):self.isMinimized=self.isMaximized=False
w=Window()
adjust_geometry(w,'窗口移动',{'X':-100,'Y':50});assert (w.left,w.top)==(-100,50)
adjust_geometry(w,'窗口移动',{'移动方式':'相对当前位置','X':20,'Y':-10});assert (w.left,w.top)==(-80,40)
adjust_geometry(w,'窗口大小',{'宽度':400,'高度':200});assert (w.left,w.top,w.width,w.height)==(-80,40,400,200)
adjust_geometry(w,'窗口大小',{'宽度':600,'高度':400,'大小锚点':'中心点'});assert (w.left,w.top)==(-180,-60)
w.isMinimized=True;adjust_geometry(w,'窗口移动',{'X':1,'Y':2});assert not w.isMinimized
for args in ({'宽度':0},{'高度':-1},{'宽度':float('nan')}):
 try:adjust_geometry(w,'窗口大小',args)
 except ValueError:pass
 else:raise AssertionError('invalid dimensions accepted')
print('PASS absolute/relative moves, both anchors, restore and invalid dimensions')
import pygetwindow
fixture=QWidget();fixture.setWindowTitle('AnClicker geometry test fixture');fixture.resize(500,350);fixture.show();app.processEvents()
try:
 target=pygetwindow.Win32Window(int(fixture.winId()))
 adjust_geometry(target,'窗口移动',{'X':100,'Y':120});app.processEvents()
 assert (target.left,target.top)==(100,120),(target.left,target.top)
 adjust_geometry(target,'窗口移动',{'移动方式':'相对当前位置','X':40,'Y':-20});app.processEvents()
 assert (target.left,target.top)==(140,100)
 adjust_geometry(target,'窗口大小',{'宽度':600,'高度':400});app.processEvents()
 assert (target.left,target.top,target.width,target.height)==(140,100,600,400)
 cx,cy=target.left+target.width/2,target.top+target.height/2
 adjust_geometry(target,'窗口大小',{'宽度':800,'高度':500,'大小锚点':'中心点'});app.processEvents()
 assert (target.width,target.height)==(800,500)
 assert abs(target.left+target.width/2-cx)<=1 and abs(target.top+target.height/2-cy)<=1
 for state in ('minimize','maximize'):
  getattr(target,state)();app.processEvents()
  adjust_geometry(target,'窗口移动',{'X':100,'Y':120});app.processEvents()
  assert not target.isMinimized and not target.isMaximized
  assert (target.left,target.top)==(100,120),(state,target.left,target.top)
 print('PASS native Windows move, relative offset, outer size and centre preservation')
finally:fixture.close();app.processEvents()
