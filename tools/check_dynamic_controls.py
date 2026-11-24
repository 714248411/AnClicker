import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='dynamic-controls-')
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.app.Start_Win import Main_window
app=QApplication([])
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
 w=Main_window(); w.resize(1500,850); w.show(); QTest.qWait(220)
 v=w.view_workspace; v.palette_collapsed=False; v.docking.sync_visibility(); v.layout_presets.apply('dynamic1')
 for width in (1500,1000,750):
  w.resize(width,850); QTest.qWait(300)
  viewport=v.controls_scroll.viewport()
  for button in (w.pushButton_5,w.pushButton_7,w.pushButton_6):
   assert button.width() >= button.sizeHint().width(), (width,button.width(),button.sizeHint().width())
   assert button.height() >= button.sizeHint().height(), (width,button.height(),button.sizeHint().height())
  assert v.controls_scroll.verticalScrollBar().maximum()==0,(width,viewport.height(),w.groupBox_3.height())
  if width<1200: assert v.docking.docks['controls'].height()>=240
 # Give the bottom panel very little height: scrolling must preserve font and access.
 v.controls_scroll.setFixedHeight(110)
 QTest.qWait(250)
 print('body name',w.groupBox_3.objectName(),'scaled',v.docking.scalers[1].last_size,'scroll',v.controls_scroll.verticalScrollBar().maximum(),'dock',v.docking.docks['controls'].height(),'viewport',v.controls_scroll.viewport().height(),'group',w.groupBox_3.height(),flush=True)
 assert v.docking.scalers[1].last_size >= 13
 assert v.controls_scroll.verticalScrollBar().maximum()>0
 v.controls_scroll.setMinimumHeight(0); v.controls_scroll.setMaximumHeight(16777215)
 v.interface_scale.change(10); QTest.qWait(300)
 for button in (w.pushButton_5,w.pushButton_7,w.pushButton_6):
  assert button.width()>=button.sizeHint().width()
 v.layout_presets.apply('dynamic2');QTest.qWait(200)
 print('PASS dynamic1 normal sizes, complete default display, short panel scrolling, larger font, switching scheme',flush=True)
 os._exit(0)
