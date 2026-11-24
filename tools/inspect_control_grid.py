import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='control-grid-')
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.app.Start_Win import Main_window
app=QApplication([])
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
 w=Main_window();w.resize(1500,900);w.show();QTest.qWait(200)
 v=w.view_workspace;v.layout_presets.apply('dynamic2');QTest.qWait(300)
 g=w.gridLayout_2
 print('group',w.groupBox_3.size(),'layout',g.count(),'rows',g.rowCount(),flush=True)
 for i in range(g.count()):
  it=g.itemAt(i); wid=it.widget(); sub=it.layout(); sp=it.spacerItem()
  print(i,g.getItemPosition(i),'widget',wid.objectName() if wid else '', 'text',wid.text() if wid and hasattr(wid,'text') else '', 'spacer',bool(sp),'layout',bool(sub),'geo',it.geometry(), 'hint',it.sizeHint(),flush=True)
 for i in (7,8):
  host=g.itemAt(i).widget(); print('HOST',i,host.sizePolicy().verticalPolicy(),host.minimumSizeHint(),host.sizeHint(),flush=True)
  for child in host.findChildren(__import__('anclicker.platform.qt_compat.QtWidgets',fromlist=['QWidget']).QWidget):
   if child.parentWidget() is host: print(' CHILD',child.objectName(),child.geometry(),child.sizeHint(),child.sizePolicy().verticalPolicy(),flush=True)
 for i in range(g.rowCount()):print('row',i,'stretch',g.rowStretch(i),'min',g.rowMinimumHeight(i),'rect',g.cellRect(i,0),flush=True)
 os._exit(0)
