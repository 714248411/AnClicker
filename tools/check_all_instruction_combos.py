import sys,tempfile,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sandbox=tempfile.TemporaryDirectory();os.environ['ANCLICKER_DATA_DIR']=sandbox.name
from types import SimpleNamespace
from anclicker.platform.qt_compat.QtWidgets import QApplication,QComboBox
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.storage.database import DatabaseOperation
from anclicker.ui.settings_combo import style_settings_combos
app=QApplication([])
db=DatabaseOperation(str(Path(sandbox.name)/'test.db'))
context=ExecutionContext(metadata={'database':db})
editors=combos=0;failures=[]
for spec in INSTRUCTION_SPECS:
 editor=None
 try:
  editor=spec.create_editor(context=context)
  style_settings_combos(editor,SimpleNamespace(view_workspace=None))
  editor.show();app.processEvents()
  for combo in editor.findChildren(QComboBox):
   if not combo.isVisible() or not combo.isEnabled() or not combo.count():continue
   combo.showPopup();app.processEvents();app.processEvents()
   view=combo.view();view.scrollToTop();app.processEvents()
   for row in range(min(combo.count(),3)):
    rect=view.visualRect(combo.model().index(row,combo.modelColumn(),combo.rootModelIndex()))
    assert view.viewport().rect().contains(rect), (spec.type_id,combo.objectName(),row,rect,view.viewport().rect())
   combos+=1;combo.hidePopup()
  editors+=1
 except Exception as error:failures.append((spec.type_id,str(error)))
 finally:
  if editor is not None:editor.hide();editor.deleteLater();app.processEvents()
print('editors',editors,'combos',combos,'failures',failures,flush=True)
if failures:raise SystemExit(1)
