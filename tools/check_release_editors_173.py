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
from anclicker.app.ui_validation import validate_instruction_editors
try:
 print(validate_instruction_editors(w))
finally:
 view.interface_scale.stop();w.ocr_pool.close();w.hide();w.deleteLater()
 from anclicker.platform.qt_compat.QtCore import QCoreApplication,QEvent
 QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
