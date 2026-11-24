import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='both-panels-')
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QDialog,QCheckBox,QLineEdit
from anclicker.platform.qt_compat.QtCore import Qt,QTimer
from anclicker.platform.qt_compat.QtTest import QTest
from anclicker.platform.qt_compat.QtGui import QKeySequence
from anclicker.app.Start_Win import Main_window
from anclicker.ui.view_shortcuts import install_view_shortcuts,SETTING
app=QApplication([])
name='指令与控制栏同时收起/展开'
with patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'):
 w=Main_window();w.resize(1400,850);w.show();QTest.qWait(200)
 v=w.view_workspace;a=w._view_shortcut_actions[name]
 assert a.property('shortcutEnabled') is False
 for p,c in ((False,False),(False,True),(True,False),(True,True)):
  if v.palette_collapsed != p:v.toggle_palette()
  v.controls_action.setChecked(not c)
  a.trigger();QTest.qWait(20)
  expected=False if p and c else True
  assert v.palette_collapsed==expected and v.controls_collapsed==expected,(p,c)
  a.trigger();QTest.qWait(20)
  assert v.palette_collapsed == (not expected) and v.controls_collapsed == (not expected)
 def inspect_dialog():
  dialog=app.activeModalWidget()
  assert isinstance(dialog,QDialog)
  box=dialog.findChild(QCheckBox,'shortcutEnabled_'+name)
  inp=dialog.findChild(QLineEdit,'shortcutInput_'+name)
  assert box and inp and not box.isChecked()
  dialog.reject()
 QTimer.singleShot(0,inspect_dialog)
 w.open_view_shortcut_settings()
 w.db.set_setting_value(SETTING,json.dumps({name:{'enabled':True,'key':'Ctrl+Alt+9'}},ensure_ascii=False))
 install_view_shortcuts(w,w.menu_4,w._view_shortcut_actions)
 assert a.shortcut().toString(QKeySequence.PortableText)=='Ctrl+Alt+9'
 print('PASS combined panel shortcut setting, all visibility states and saved key',flush=True)
 os._exit(0)
