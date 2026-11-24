import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='schedule-chrome-')
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
 w=Main_window();w.resize(1400,900);w.show();QTest.qWait(150)
 bar=w.view_workspace.title_bar
 assert bar.schedule_button.isVisible() and not bar.schedule_button.icon().isNull()
 assert bar.schedule_button.x() < bar.theme_button.x() < bar.minBtn.x()
 assert not hasattr(w.workspace.palette,'schedule_button')
 bar.schedule_button.click();QTest.qWait(250)
 dialog=w.task_scheduler.dialog
 assert dialog and dialog.isVisible()
 assert dialog.advanced_button.isChecked() and dialog.advanced_scroll.isVisible()
 assert dialog.advanced_scroll.height()>0
 assert dialog.save_button.parentWidget() is dialog.advanced
 assert dialog.save_button.mapTo(dialog,dialog.save_button.rect().topLeft()).y() >= dialog.random_end.mapTo(dialog,dialog.random_end.rect().bottomLeft()).y()
 assert dialog.random_tip.mapTo(dialog,dialog.random_tip.rect().topLeft()).y() > dialog.save_button.mapTo(dialog,dialog.save_button.rect().bottomLeft()).y()
 assert dialog.save_button.isEnabled()
 dialog.advanced_button.setChecked(False);QTest.qWait(100)
 assert not dialog.advanced_scroll.isVisible()
 assert dialog.save_button.parentWidget() is dialog.editor_panel
 assert abs(dialog.save_button.mapTo(dialog,dialog.save_button.rect().topLeft()).y()-dialog.advanced_button.mapTo(dialog,dialog.advanced_button.rect().topLeft()).y())<4
 dialog.advanced_button.setChecked(True);QTest.qWait(100)
 assert dialog.advanced_scroll.isVisible()
 dialog.random_enabled.setChecked(True)
 assert dialog.when.isHidden() and dialog.random_range.isEnabled()
 for mode in ('dark','light'):
  bar.apply_theme(mode,w.view_workspace.THEMES[mode])
  assert not bar.schedule_button.icon().isNull()
 print('PASS titlebar scheduling, default advanced expansion, bottom save, collapse, random settings and both themes',flush=True)
 os._exit(0)
