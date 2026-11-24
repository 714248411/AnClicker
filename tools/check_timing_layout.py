import sys,tempfile,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
sandbox=tempfile.TemporaryDirectory();os.environ['ANCLICKER_DATA_DIR']=sandbox.name
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMessageBox,QLabel,QComboBox
from anclicker.app.Start_Win import Main_window
from anclicker.storage.database import DatabaseOperation
from anclicker.instructions.registry import get_instruction_spec
app=QApplication([]);db=DatabaseOperation(str(Path(sandbox.name)/'test.db'))
with patch('anclicker.app.Start_Win.DatabaseOperation',return_value=db),patch('anclicker.app.main_work.DatabaseOperation',return_value=db),patch('anclicker.app.Start_Win.SystemHotkey'),patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'),patch.object(Main_window,'_install_updates'):
 w=Main_window()
w.register_global_shortcut_keys=lambda:None;w.unregister_global_shortcut_keys=lambda:None
w.show();app.processEvents()
view=w.view_workspace
from anclicker.execution.execution_timing import AdvancedTimingDialog
from anclicker.platform.qt_compat.QtCore import QCoreApplication,QEvent
from anclicker.platform.qt_compat.QtWidgets import QPushButton
for theme in ('light','dark'):
 view.theme_mode=theme;view._apply_theme()
 for delta in (0,3,-2):
  view.interface_scale.change(None)
  if delta:view.interface_scale.change(delta)
  dialog=AdvancedTimingDialog(w,db);dialog.show()
  app.processEvents();app.processEvents()
  for b in dialog.findChildren(QPushButton):
   if b.isVisible() and b.text():
    assert b.height()>=b.fontMetrics().height()+8,(b.text(),b.height())
  for spin in dialog.spins.values():spin.setValue(1.25)
  dialog.reset_button.click()
  assert all(spin.value()==0 for spin in dialog.spins.values())
  if delta==0:dialog.grab().save('artifacts/validation/timing-'+theme+'.png')
  dialog.reject();dialog.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
view.interface_scale.stop();w.ocr_pool.close();w.hide();w.deleteLater()
QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
print('PASS timing layout and reset, both themes, three font sizes')
