import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='table-tips-center-')
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
 w=Main_window(); w.resize(1500,900);w.show();QTest.qWait(200)
 v=w.view_workspace
 tips=v.table_tips
 assert not tips.expanded and tips.isHidden()
 assert v.table_header.contextMenuPolicy()
 tips.set_expanded(True);QTest.qWait(100)
 assert tips.isVisibleTo(v.table_header)
 g=tips.geometry(); parent=v.table_header.width()
 assert g.width()<=680
 assert abs(g.center().x()-parent/2)<70,(g,parent)
 tips.set_expanded(False); assert tips.isHidden()
 assert w.db.get_setting_value('显示表格操作提示')=='False'
 print('PASS default hidden, reopen and hide, centered bounded prompt, preference persistence',flush=True)
 os._exit(0)
