import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp()
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QTabBar,QLabel
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.platform.qt_compat.QtCore import Qt,QPoint
from anclicker.app.Start_Win import Main_window
app=QApplication([])
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
 w=Main_window();w.resize(800,850);w.show();QTest.qWait(200)
 v=w.view_workspace;v.palette_collapsed=False;v.docking.sync_visibility();v.layout_presets.apply('dynamic2');QTest.qWait(400)
 d=v.docking
 for bar in d.host.findChildren(QTabBar):
  print('bar',bar.objectName(),'parent',bar.parent().objectName(),'geom',bar.geometry(),'base',bar.drawBase(),'tabs',[bar.tabText(i) for i in range(bar.count())],flush=True)
  if bar.count() and '快捷指令' in [bar.tabText(i) for i in range(bar.count())]:
   d.docks['controls'].raise_();QTest.qWait(200)
   print('tab pos',bar.mapTo(w,bar.tabRect(0).topLeft()),'button pos',w.pushButton_6.mapTo(w,QPoint()),flush=True)
   for label in w.groupBox_3.findChildren(QLabel):
    if label.text().startswith('最近项目'):print('recent label',label.mapTo(w,QPoint()),'button',w.pushButton_6.mapTo(w,QPoint()),flush=True)
   w.grab().save(str(Path(os.environ['ANCLICKER_DATA_DIR'])/'screen.png'));print('image',str(Path(os.environ['ANCLICKER_DATA_DIR'])/'screen.png'),flush=True)
 os._exit(0)
