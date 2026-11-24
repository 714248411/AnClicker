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
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.app.Start_Win import Main_window
app=QApplication([])
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
 w=Main_window(); w.resize(1500,900); w.show(); QTest.qWait(200)
 v=w.view_workspace; v.palette_collapsed=False;v.docking.sync_visibility();v.layout_presets.apply('dynamic1')
 for width in (1500,1000,750):
  w.resize(width,850);QTest.qWait(350)
  g=w.groupBox_3; sc=v.controls_scroll; d=v.docking.docks['controls']
  print('width',width,'host',v.docking.host.width(),'dock',d.width(),d.height(),'scroll',sc.viewport().width(),sc.viewport().height(),'body',g.width(),g.height(),'hint',g.sizeHint().width(),g.sizeHint().height(),'minimum',g.minimumSizeHint().width(),g.minimumSizeHint().height(),'horizontal',v.docking.controls_horizontal,'vscroll',sc.verticalScrollBar().maximum(), 'hscroll',sc.horizontalScrollBar().maximum(),flush=True)
  if width==1000: w.groupBox_3.grab().save(str(Path(os.environ['ANCLICKER_DATA_DIR'])/'controls.png')); print('PREVIEW',str(Path(os.environ['ANCLICKER_DATA_DIR'])/'controls.png'),flush=True)
  for c in (w.pushButton_5,w.pushButton_7,w.pushButton_6,w.checkBox_2,w.run_unconnected_checkbox):
   print(c.objectName(),c.text(),c.width(),c.height(),'hint',c.sizeHint().width(),c.sizeHint().height(),flush=True)
 os._exit(0)
