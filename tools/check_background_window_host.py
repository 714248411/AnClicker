import sys,faulthandler,gc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
faulthandler.enable()
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.registry import get_instruction_spec
from anclicker.ui.settings_combo import style_settings_combos
from anclicker.ui.adaptive_panels import AdaptivePanelSizer
from anclicker.ui.dock_workspace import ParameterPinFilter
from anclicker.platform.background_catalog import group_methods,label
from types import SimpleNamespace
import tempfile,os
from unittest.mock import patch
sandbox=tempfile.TemporaryDirectory()
os.environ['ANCLICKER_DATA_DIR']=sandbox.name
from anclicker.app.Start_Win import Main_window
from anclicker.storage.database import DatabaseOperation
app=QApplication([])
db=DatabaseOperation(str(Path(sandbox.name)/'test.db'))
with patch('anclicker.app.Start_Win.DatabaseOperation',return_value=db),patch('anclicker.app.main_work.DatabaseOperation',return_value=db),patch('anclicker.app.Start_Win.SystemHotkey'),patch.object(Main_window,'register_global_shortcut_keys'),patch.object(Main_window,'unregister_global_shortcut_keys'),patch.object(Main_window,'_install_updates'):
 window=Main_window()
window.register_global_shortcut_keys=lambda:None
window.unregister_global_shortcut_keys=lambda:None
window.show();app.processEvents()
owner=SimpleNamespace(view_workspace=None)
for turn in range(3):
 print('create',turn,flush=True)
 editor=get_instruction_spec('后台窗口操作').create_editor(parent=window,context=ExecutionContext())
 editor._pin_filter=ParameterPinFilter(editor)
 editor._panel_scaler=AdaptivePanelSizer(editor,editor,600,reference_height=420,base_pixels=13)
 print('theme',flush=True)
 style_settings_combos(editor,owner)
 editor.setStyleSheet('QWidget {background:#242424;color:white;} QComboBox {padding:4px;}')
 window.workspace._run_parameter_editor(editor,lambda draft:None,'crash-test-'+str(turn));app.processEvents()
 combo=editor._controls['接口']
 for name in group_methods('后台窗口操作'):
  print('method',name,flush=True)
  combo.setCurrentText(label(name));editor.resize(500+turn*50,450);editor._panel_scaler.last_size=None;app.processEvents()
  editor.get_draft()
  editor.advanced_button.setChecked(True);app.processEvents()
  combo.showPopup();app.processEvents();combo.hidePopup()
  combo.completer().setCompletionPrefix('窗口');combo.completer().complete();app.processEvents();combo.completer().popup().hide()
 editor.reject();app.processEvents();gc.collect()
print('PASS background window settings lifecycle',flush=True)

window.ocr_pool.close()
window.hide()
