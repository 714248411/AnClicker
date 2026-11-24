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
from anclicker.ui.workspace_constants import TABLE_VIEW
view.tabs.setCurrentIndex(TABLE_VIEW)
app.processEvents();app.processEvents()
for theme in ('light','dark'):
 view.theme_mode=theme;view._apply_theme()
 for delta in (0,3,-2):
  view.interface_scale.change(None)
  if delta:view.interface_scale.change(delta)
  app.processEvents();app.processEvents()
  header=view.command_table.horizontalHeader()
  assert header.height()>=view.tabs.tabBar().height()+4
  assert header.height()>=header.fontMetrics().height()+10
  assert header.height()>=header.sizeHint().height()-2
  print(theme, delta, header.height(), header.fontMetrics().height())
  assert view.table_state.text()=='共 0 条指令',view.table_state.text()
  if delta == 0:
   output=Path(__file__).resolve().parents[1]/'artifacts'/'validation'
   output.mkdir(parents=True,exist_ok=True)
   view.table_page.grab().save(str(output/f'table-header-{theme}.png'))
  label=view.table_state
  assert label.geometry().right()>=label.parentWidget().width()-20
view.interface_scale.stop();w.ocr_pool.close();w.hide();app.processEvents()
w.deleteLater()
from anclicker.platform.qt_compat.QtCore import QCoreApplication,QEvent
QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
app.processEvents()
print('PASS count text/right alignment and table header height across themes/font sizes')
