"""Configurable secondary runtime stop hotkey and settings regression."""
import sys,tempfile,sqlite3
from pathlib import Path
from unittest.mock import patch,Mock
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtGui import QKeyEvent
from anclicker.storage.database import DatabaseOperation
from anclicker.ui.dialogs.设置窗口 import Setting
from anclicker.app.Start_Win import Main_window
from anclicker.platform.services import normalize_hotkey

class Hotkeys:
 supported=True
 def __init__(self):self.callbacks={};self.removed=[]
 def register(self,keys,callback,overwrite=False):self.callbacks[tuple(keys)]=callback
 def unregister(self,keys):self.removed.append(tuple(keys));self.callbacks.pop(tuple(keys),None)

def main():
 configure_application();app=QApplication.instance() or QApplication([])
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'task.db';db=DatabaseOperation(str(path))
  assert db.get_global_shortcut()['结束运行2']==[]
  with sqlite3.connect(path) as connection:connection.execute('DELETE FROM 设置 WHERE 设置项=?',('快捷键-结束运行2',))
  connection.close()
  assert db.get_global_shortcut()['结束运行2']==[]
  assert DatabaseOperation(str(path)).get_global_shortcut()['结束运行2']==[]
  hk=Hotkeys()
  with patch('anclicker.app.Start_Win.DatabaseOperation',return_value=db),patch('anclicker.app.main_work.DatabaseOperation',return_value=db),patch('anclicker.app.Start_Win.SystemHotkey',return_value=hk),patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'_install_updates'):
   w=Main_window()
  w.resize(1100,720);w.show();app.processEvents()
  with patch('anclicker.app.Start_Win.is_hotkey_valid',return_value=True),patch('anclicker.ui.dialogs.设置窗口.is_hotkey_valid',return_value=True),patch('anclicker.ui.dialogs.设置窗口.create_system_hotkey',return_value=hk):
   w.register_global_shortcut_keys();assert ('escape',) not in hk.callbacks
   settings=Setting(w);settings.tabWidget.setCurrentWidget(settings.tab_3);settings.show();app.processEvents()
   assert settings.keySequenceEdit_3.keySequence().isEmpty()
   assert settings.gridLayout_6.getItemPosition(settings.gridLayout_6.indexOf(settings.keySequenceEdit_3))[:2]==(2,1)
   for key,text,expected in ((Qt.Key_A,'a','A'),(Qt.Key_F9,'','F9'),(Qt.Key_Escape,'','Esc')):
    settings.keySequenceEdit_3.clear();settings.keySequenceEdit_3.setFocus();app.processEvents()
    QApplication.sendEvent(settings.keySequenceEdit_3,QKeyEvent(QKeyEvent.KeyPress,key,Qt.NoModifier,text))
    QApplication.sendEvent(settings.keySequenceEdit_3,QKeyEvent(QKeyEvent.KeyRelease,key,Qt.NoModifier,text))
    assert settings.keySequenceEdit_3.keySequence().toString()==expected
   settings.keySequenceEdit_3.setKeySequence('Ctrl+F9');settings.save_setting_date();settings.close();app.processEvents()
   assert DatabaseOperation(str(path)).get_global_shortcut()['结束运行2']==['ctrl','f9']
   assert w.escape_stop.key().toString()=='Ctrl+F9' and ('control','f9') not in hk.callbacks
   assert w._arm_escape_stop();assert ('control','f9') in hk.callbacks and ('escape',) not in hk.callbacks
   with patch.object(w.command_thread,'isRunning',return_value=True),patch.object(w.command_thread,'request_stop') as stop,patch.object(w.task_scheduler,'stop') as scheduler_stop,patch.object(db,'system_prompt_tone'):
    hk.callbacks[('control','f9')](None);app.processEvents();stop.assert_called_once();scheduler_stop.assert_called_once()
   w._runtime_finished();assert ('control','f9') not in hk.callbacks and not w.escape_stop.isEnabled()
   for key,expected in [('A',('a',)),('F9',('f9',)),('Ctrl+Alt+F9',('control','alt','f9')),('Esc',('escape',))]:
    db.set_global_shortcut(**{'结束运行2':key.lower().split('+')});w.register_global_shortcut_keys();assert w._arm_escape_stop();assert expected in hk.callbacks
    w._runtime_finished();assert expected not in hk.callbacks
   with patch.object(w.task_scheduler,'active',{'id':'test'}):
    w._sync_stop_shortcut();assert ('escape',) in hk.callbacks
    w._runtime_finished();assert ('escape',) in hk.callbacks
   w._sync_stop_shortcut();assert ('escape',) not in hk.callbacks
   settings=Setting(w);settings.tabWidget.setCurrentWidget(settings.tab_3);settings.keySequenceEdit_3.setKeySequence('F9')
   settings.restore_default_shortcuts();assert settings.keySequenceEdit_3.keySequence().isEmpty()
   before=db.get_global_shortcut()
   for sequence in ('F10','Ctrl+K, Ctrl+C'):
    settings.keySequenceEdit_3.setKeySequence(sequence)
    with patch('anclicker.ui.dialogs.设置窗口.QMessageBox.information'):
     try:settings.save_setting_date()
     except ValueError:pass
     else:raise AssertionError('invalid shortcut accepted: '+sequence)
    assert db.get_global_shortcut()==before
   settings.restore_default_shortcuts();settings.save_setting_date()
   assert DatabaseOperation(str(path)).get_global_shortcut()['结束运行2']==[]
   settings.close();app.processEvents()
   assert w._arm_escape_stop() and not w.escape_stop.isEnabled()
   assert ('escape',) not in hk.callbacks
   settings=Setting(w);assert settings.keySequenceEdit_3.keySequence().isEmpty()
   for mode in ('light','dark'):
    w.view_workspace.theme_mode=mode;w.view_workspace._apply_theme();settings.close();settings=Setting(w);settings.tabWidget.setCurrentWidget(settings.tab_3);settings.show();app.processEvents()
    assert settings.keySequenceEdit_3.isVisible()
    settings.grab().save('artifacts/validation/stop2-shortcut-'+mode+'.png')
   settings.close();app.processEvents();w.unregister_global_shortcut_keys();assert not hk.callbacks
  w.close();w.ocr_pool.close();app.processEvents()
 print('PASS legacy defaults, four settings fields, persistence/reset/invalid key guards, runtime-only Esc/single key/combo registration, actual stop callback and cleanup; dark/light UI')
 return 0

if __name__=='__main__':raise SystemExit(main())
