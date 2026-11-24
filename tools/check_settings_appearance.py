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
editor=get_instruction_spec('后台窗口操作').create_editor(parent=w)
w.workspace._run_parameter_editor(editor,lambda d:None,'parameters_appearance')
app.processEvents()
for theme in ('light','dark'):
 view.theme_mode=theme;view._apply_theme();app.processEvents()
 view.docking.reset_parameter_sizes();app.processEvents();app.processEvents()
 for offset in (0,3,-2,0):
  view.interface_scale.change(None)
  if offset:view.interface_scale.change(offset)
  app.processEvents()
  widgets=[editor.ui.label_0,editor._controls['接口'],editor.repeat_count]
  sizes=[widget.font().pixelSize() for widget in widgets]
  assert sizes==[14+offset]*len(sizes),(theme,offset,sizes)

 box=QMessageBox(w);box.setStandardButtons(QMessageBox.Yes|QMessageBox.No);box.show();app.processEvents()
 print('button',repr(box.button(QMessageBox.Yes).text()),'listening',view.interface_scale.listening,'owns',view.interface_scale.owns(box),flush=True)
 assert box.button(QMessageBox.Yes).text().replace('&','')=='是'
 assert box.button(QMessageBox.No).text().replace('&','')=='否'
 assert view.THEMES[theme]['surface'] in box.styleSheet()
 box.hide();box.deleteLater()
dock=view.docking.docks['parameters_appearance']
dock.resize(320,260);app.processEvents();app.processEvents()
assert editor._controls['接口'].font().pixelSize()<=14
for action in (view.restore_size_action,view.restore_view_action):
 action.trigger();app.processEvents();app.processEvents()
 assert view.interface_scale.offset==0
 assert editor._controls['接口'].font().pixelSize()==14,editor._controls['接口'].font().pixelSize()
editor.reject();view.interface_scale.stop();w.ocr_pool.close();w.hide();app.processEvents()
print('PASS: light/dark settings, uniform 14px with interface offsets, shrink and reset, Chinese yes/no', flush=True)
# This isolated harness keeps mocked Qt window services alive; avoid interpreter-order Qt destruction.
os._exit(0)
