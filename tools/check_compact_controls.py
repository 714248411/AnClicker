import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='compact-controls-')
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QComboBox
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.app.Start_Win import Main_window
app=QApplication([])
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
 w=Main_window();w.resize(1500,900);w.show();QTest.qWait(200)
 v=w.view_workspace;v.palette_collapsed=False;v.docking.sync_visibility();v.layout_presets.apply('dynamic2');QTest.qWait(250)
 def check():
  combo=w.groupBox_3.findChild(QComboBox,'recentProjectsCombo')
  combo_bottom=combo.mapTo(w.groupBox_3,combo.rect().bottomLeft()).y()
  start_top=w.pushButton_5.mapTo(w.groupBox_3,w.pushButton_5.rect().topLeft()).y()
  assert 0<=start_top-combo_bottom<=36,(combo_bottom,start_top)
  for b in (w.pushButton_5,w.pushButton_7,w.pushButton_6):
   assert b.height()>=b.sizeHint().height()
 check()
 v.interface_scale.change(8);QTest.qWait(350);check()
 v.interface_scale.change(None);QTest.qWait(200)
 d=v.docking
 d.move_panel('controls','bottom');QTest.qWait(200)
 d.move_panel('controls','left');QTest.qWait(200);check()
 print('PASS compact project/button spacing, large fonts and horizontal-to-vertical transition',flush=True)
 os._exit(0)
