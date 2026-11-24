"""Regression for nested settings dialogs and fixed/following image regions."""
import sys, tempfile, time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtCore import QTimer, Qt
from anclicker.domain.instructions import ExecutionContext
from anclicker.ui.instruction_editors.其他.窗口排布 import InstructionEditor as Arrangement
from anclicker.ui.instruction_editors.键鼠.图像点击 import InstructionEditor as ImageEditor
from anclicker.ui.timing_dialog import open_advanced_timing
from anclicker.platform.image_region import window_region, region_in_bound_window
from anclicker.execution import actions
from PIL import Image

class DB:
    def __init__(self): self.saved={}
    def get_setting_value(self,k): return self.saved.get(k,'')
    def update_settings(self,**kw): self.saved.update(kw)
    def extract_resource_folder_path(self): return []
    def get_variable_info(self,*a): return {}
class Windows:
    def __init__(self): self.rect=(10,20,110,220); self.gui=self; self.minimized=False
    def resolve(self,t):
        if not t: raise ValueError('missing window')
        return t
    def validate(self,t): pass
    def IsIconic(self,h): return self.minimized
    def IsWindowVisible(self,h): return True
    def GetWindowRect(self,h): return self.rect
    def ClientToScreen(self,h,p): return (20,30)
    def size(self,t): return SimpleNamespace(width=80,height=100)
app=QApplication([]); app.setQuitOnLastWindowClosed(False)
db=DB(); context=ExecutionContext(metadata={'database':db})
e=Arrangement(context=context);e.show();app.processEvents()
started=time.monotonic();d=open_advanced_timing(e,db)
assert time.monotonic()-started < 3
assert open_advanced_timing(e,db) is d
heartbeat=[];QTimer.singleShot(10,lambda:heartbeat.append(True))
end=time.monotonic()+2
while (not heartbeat or not d.isVisible()) and time.monotonic()<end: app.processEvents()
assert heartbeat and d.isVisible()
d.spins['统一指令间隔'].setValue(.123);d.accept();app.processEvents()
assert db.saved['统一指令间隔']=='0.123' and e._advanced_timing_dialog is None
d=open_advanced_timing(e,db);d.spins['统一指令间隔'].setValue(2);d.reject();app.processEvents()
assert db.saved['统一指令间隔']=='0.123'
e.close()
target={'窗口句柄':'123','窗口标题':'Test','窗口类名':'TestClass','进程ID':10}
w=Windows()
with patch('anclicker.platform.image_region.current_backend',return_value=None):
 assert window_region(target,w)==(10,20,100,200)
 w.rect=(-20,40,180,140)
 assert window_region(target,w)==(-20,40,200,100)
 assert region_in_bound_window((-20,40,200,100),target,w)==(0,10,80,90)
 assert window_region(dict(target,区域偏移=[5,10,-15,-20]),w)==(-15,50,180,70)
 w.rect=(100,200,300,300)
 assert window_region(dict(target,区域偏移=[5,10,-15,-20]),w)==(105,210,180,70)
 w.minimized=True
 try: window_region(target,w); raise AssertionError('minimized allowed')
 except ValueError: pass
seen=[]
with patch.object(actions,'resolve_image_path',return_value='test.png'),patch.object(actions,'window_region',side_effect=[(1,2,3,4),(11,12,30,40)]),patch.object(actions,'locate_image_on_screen',side_effect=lambda p,**kw:seen.append(kw['region']) or SimpleNamespace(x=1,y=2)):
 for _ in range(2):actions.locate_image({'区域模式':'跟随窗口','区域窗口':target},context)
assert seen==[(1,2,3,4),(11,12,30,40)]
with tempfile.TemporaryDirectory() as tmp:
 path=Path(tmp)/'image.png';Image.new('RGB',(10,10)).save(path)
 editor=ImageEditor(context=context,draft={'type_id':'图像点击','parameters':{'图像路径':str(path),'区域':'(10,20,100,200)','区域模式':'跟随窗口','区域窗口':target}})
 editor.tabs.currentChanged.disconnect(editor._region_preview_tab_changed)
 assert editor.ui.auxiliary_3.text()=='框选固定区域'
 assert editor.follow_region_button.text()=='跟随窗口区域'
 assert editor.get_draft().parameters['区域窗口']==target
 with patch('anclicker.ui.instruction_editors.image_click_editor.pick_background_window',return_value=None):editor._pick_follow_region()
 assert editor._region_target==target
 editor.follow_region_group.setChecked(False)
 assert '区域窗口' not in editor.get_draft().parameters and editor.get_draft().parameters['区域']==''
 with patch('anclicker.ui.instruction_editors.image_click_editor.pick_fixed_region',return_value=(-100,20,80,90)):
  editor._run_auxiliary('区域')
 assert not editor.follow_region_group.isChecked() and editor.get_draft().parameters['区域']=='(-100, 20, 80, 90)'
 assert not editor.ui.parameter_3.isReadOnly()
 assert editor.region_group.title()=='启动区域识别'
 assert editor.follow_region_group.title()=='启动区域识别2'
 editor.follow_region_group.setChecked(True)
 assert not editor.region_group.isChecked() and editor.get_draft().parameters['区域窗口']==target
 editor.show();app.processEvents()
 assert abs(editor.region_group.width()-editor.follow_region_group.width()) <= 1
 from anclicker.ui.instruction_editors.compact_settings import compact_body
 from anclicker.platform.qt_compat.QtCore import QPoint
 for width in (760,1000):
  editor.resize(width,800)
  compact_body(editor._parameter_body);app.processEvents()
  buttons=(editor.ui.auxiliary_6,editor.ui.auxiliary_3,editor.follow_region_button)
  bottoms=[button.mapTo(editor,QPoint(0,button.height())).y() for button in buttons]
  assert max(bottoms)-min(bottoms)<=1, bottoms

 editor.tabs.setCurrentWidget(editor.region_preview_page)
 with patch('anclicker.ui.instruction_editors.image_click_editor.window_region',return_value=(10,20,100,200)):
  editor._update_region_preview()
 editor._preview_region_changed((20,40,50,100))
 assert editor.get_draft().parameters['区域窗口']['区域偏移']==[10,20,-40,-80]
 assert [spin.value() for spin in editor.region_offset_spins]==[10,20,-40,-80]
 with patch('anclicker.ui.instruction_editors.image_click_editor.window_region',return_value=(10,20,100,200)):
  editor.region_offset_spins[0].setValue(12)
 assert editor.get_draft().parameters['区域窗口']['区域偏移']==[12,20,-40,-80]
 saved=editor.get_draft();editor.load_draft(saved)
 assert editor._region_target['区域偏移']==[12,20,-40,-80]
 editor.region_group.setChecked(True)
 editor.tabs.setCurrentWidget(editor.region_preview_page);editor._update_region_preview()
 from anclicker.platform.qt_compat.QtCore import QPointF
 canvas=editor.region_preview
 rect=canvas.display_rect(canvas.region)
 class Drag:
  def __init__(self,p):self.p=p
  def button(self):return Qt.LeftButton
  def position(self):return self.p
  def accept(self):pass
 before=actions.region(editor.ui.parameter_3.text())
 canvas.mousePressEvent(Drag(QPointF(rect.right(),rect.center().y())))
 canvas.mouseMoveEvent(Drag(QPointF(rect.right()+15,rect.center().y())))
 canvas.mouseReleaseEvent(Drag(QPointF(rect.right()+15,rect.center().y())))
 after=actions.region(editor.ui.parameter_3.text())
 assert after[2]>before[2] and after[:2]==before[:2]
 canvas.set_region((0,0,800,600),(100,100,300,200))
 rect=canvas.display_rect(canvas.region)
 start=rect.center()
 canvas.mousePressEvent(Drag(start))
 assert canvas.drag_edges=='move'
 canvas.mouseMoveEvent(Drag(QPointF(start.x()+20,start.y()+10)))
 canvas.mouseReleaseEvent(Drag(start))
 moved=actions.region(editor.ui.parameter_3.text())
 assert moved[2:]==(300,200) and moved[0]>100 and moved[1]>100
 assert editor.confidence_slider.width()>editor.region_group.width()*.7
 assert editor.tabs.tabText(editor.tabs.indexOf(editor.preview)+1)=='区域预览'
 from PySide2.QtTest import QTest
 canvas.mouseDoubleClickEvent(Drag(QPointF(40,40)));app.processEvents()
 full=canvas._fullscreen_dialog
 assert full is not None and full.isFullScreen()
 from anclicker.ui.region_preview import RegionPreview
 large=full.findChild(RegionPreview)
 large.region_changed.emit((10,20,80,90))
 assert actions.region(editor.ui.parameter_3.text())==(10,20,80,90)
 QTest.keyClick(full,Qt.Key_Escape);app.processEvents()
 assert canvas._fullscreen_dialog is None and editor.isVisible()
 canvas.mouseDoubleClickEvent(Drag(QPointF(40,40)));app.processEvents()
 assert canvas._fullscreen_dialog.isFullScreen()
 QTest.keyClick(canvas._fullscreen_dialog,Qt.Key_Escape);app.processEvents()
 from anclicker.platform.qt_compat.QtGui import QPixmap
 pixmap=QPixmap(800,600);pixmap.fill(Qt.gray)
 with patch('anclicker.ui.region_screenshot.capture_desktop',return_value=(pixmap,(0,0,800,600))):
  editor._capture_region_preview()
  until=time.monotonic()+.3
  while time.monotonic()<until: app.processEvents()
 assert canvas._fullscreen_dialog is not None
 assert canvas._fullscreen_dialog.findChild(RegionPreview).background_image is not None
 assert editor.windowOpacity()>0 and editor.region_screenshot_button.isEnabled()
 QTest.keyClick(canvas._fullscreen_dialog,Qt.Key_Escape);app.processEvents()
 assert canvas._fullscreen_dialog is None
 editor.tabs.setCurrentWidget(editor.preview)
 editor.tabs.currentChanged.connect(editor._region_preview_tab_changed)
 with patch('anclicker.ui.region_screenshot.capture_desktop',return_value=(pixmap,(-100,0,800,600))) as capture_mock:
  editor.tabs.setCurrentWidget(editor.region_preview_page)
  until=time.monotonic()+.3
  while time.monotonic()<until: app.processEvents()
  assert capture_mock.call_count==1 and canvas._fullscreen_dialog is None
  editor._update_region_preview();editor._update_region_preview()
  assert capture_mock.call_count==1
  with patch('anclicker.ui.instruction_editors.image_click_editor.window_region',return_value=(10,20,100,200)):
   editor.follow_region_group.setChecked(True)
   editor._update_region_preview()
  assert canvas.area.x()==-100 and canvas.area.width()==800
 editor.grab().save(str(Path(__file__).resolve().parents[1]/'artifacts/validation/image-region-preview.png'))
 editor.close()
from anclicker.ui.image_region_picker import ImageRegionPicker
from anclicker.platform.qt_compat.QtCore import QPointF
class Event:
 def __init__(self,x,y,button=Qt.LeftButton):self.p=QPointF(x,y);self.b=button
 def button(self):return self.b
 def buttons(self):return self.b
 def modifiers(self):return Qt.NoModifier
 def position(self):return self.p
 def accept(self):pass
w=Windows();w.cursor_position=lambda:(20,30);w.at_point=lambda p,child=False:target
with patch('anclicker.ui.background_window_picker.Windows',return_value=w),patch('anclicker.platform.image_region.current_backend',return_value=None):
 picker=ImageRegionPicker();picker.mousePressEvent(Event(20,30));picker.mouseReleaseEvent(Event(20,30))
 assert picker.region==(10,20,100,200)
 picker=ImageRegionPicker();picker.mousePressEvent(Event(20,30));w.cursor_position=lambda:(80,100)
 picker.mouseMoveEvent(Event(80,100));picker.mouseReleaseEvent(Event(80,100))
 assert picker.region==(20,30,60,70)
 picker=ImageRegionPicker();picker.mouseReleaseEvent(Event(0,0,Qt.RightButton));assert picker.region is None
print('PASS: fixed picker click/drag/cancel')
print('PASS: settings heartbeat/save/cancel/reopen; region movement, background coordinates, minimized rejection, editor roundtrip/cancel/disable/fixed')
