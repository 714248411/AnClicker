import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='tooltip-policy-')
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QLabel,QDialog
from anclicker.platform.qt_compat.QtCore import QPoint,QEvent
from anclicker.platform.qt_compat.QtGui import QHelpEvent
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.app.Start_Win import Main_window
from anclicker.ui.tooltip_policy import TooltipPolicy,SHOW_ALL,SHOW_LONG
app=QApplication([])
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
 w=Main_window();w.resize(900,800);w.show();QTest.qWait(120)
 p=w.tooltip_policy; assert p.show_all and not p.show_long
 assert not p.long_action.isChecked()
 assert '显示悬浮提示' in [a.text() for a in w.menu_2.actions()]
 assert '显示过长悬浮提示' in [a.text() for a in w.menu_2.actions()]
 label=QLabel('x',w);label.setToolTip('短提示')
 event=QHelpEvent(QEvent.ToolTip,QPoint(0,0),QPoint(0,0))
 assert p.allow('短提示',label)
 assert not p.allow('<span style="font-size:2000px">超大</span>',label)
 for i in range(160): p.allow('提示'+str(i),label)
 assert len(p._measurements)<=128
 import time,json
 p._measurements.clear()
 text='重复悬停提示，包含说明内容。'*10
 start=time.perf_counter()
 for i in range(500):
  p._measurements.clear();p.allow(text,label)
 uncached=time.perf_counter()-start
 start=time.perf_counter()
 for i in range(500):p.allow(text,label)
 cached=time.perf_counter()-start
 print(json.dumps({'uncached_ms':uncached*1000,'cached_ms':cached*1000}),flush=True)
 assert not p.allow('长提示'*1000,label)
 assert not p.allow('很长的一行'*1000+'\n第二行',label)
 label.setToolTip('长提示'*1000)
 assert p.eventFilter(label,event)
 p.long_action.setChecked(True)
 assert p.allow('长提示'*1000,label)
 assert not p.eventFilter(label,event)
 p.all_action.setChecked(False)
 assert not p.allow('短提示',label)
 assert p.eventFilter(label,event)
 assert w.db.get_setting_value(SHOW_ALL)=='False'
 assert w.db.get_setting_value(SHOW_LONG)=='True'
 restored=TooltipPolicy(w)
 assert not restored.show_all and restored.show_long
 restored.all_action.setChecked(True); restored.long_action.setChecked(False)
 dialog=QDialog(w);dialog.resize(300,200)
 child=QLabel(dialog)
 assert not restored.allow('长'*100,child)
 assert restored.owns(child)
 print('PASS help switches, defaults, short/long and multiline filtering, nested dialog and persistence',flush=True)
 os._exit(0)
