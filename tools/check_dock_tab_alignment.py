import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='dock-tab-alignment-')
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QTabBar,QLabel
from anclicker.platform.qt_compat.QtCore import QPoint
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.app.Start_Win import Main_window
app=QApplication([])
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
 w=Main_window();w.resize(800,850);w.show();QTest.qWait(200)
 v=w.view_workspace;v.palette_collapsed=False;v.docking.sync_visibility();v.layout_presets.apply('dynamic2');QTest.qWait(300)
 d=v.docking;d.docks['controls'].raise_();QTest.qWait(100)
 bar=next(x for x in d.host.findChildren(QTabBar) if x.parent()==d.host and x.count()==2)
 label=next(x for x in w.groupBox_3.findChildren(QLabel) if x.text().startswith('最近项目'))
 button_x=w.pushButton_6.mapTo(w,QPoint()).x()
 assert label.mapTo(w,QPoint()).x()==button_x
 assert abs((bar.mapTo(w,bar.tabRect(0).topLeft()).x()+8)-button_x)<=2
 for theme in ('dark','light'):
  if v.theme_mode!=theme:v.toggle_theme()
  QTest.qWait(100)
  assert not bar.drawBase()
  assert 'margin-left: 8px' in w.styleSheet()
  assert label.mapTo(w,QPoint()).x()==w.pushButton_6.mapTo(w,QPoint()).x()
  bar.setCurrentIndex(0);bar.setCurrentIndex(1);QTest.qWait(50)
 print('PASS dock tabs no baseline, aligned labels/buttons/tabs, theme changes and tab switching',flush=True)
 os._exit(0)
