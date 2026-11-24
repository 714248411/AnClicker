import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.domain.instructions import ExecutionContext
from anclicker.storage.database import DatabaseOperation
app=QApplication([])
errors=[]
with tempfile.TemporaryDirectory() as folder:
 db=DatabaseOperation(str(Path(folder)/'test.db'))
 for spec in INSTRUCTION_SPECS:
  try:
   editor=spec.create_editor(context=ExecutionContext(metadata={'database':db}));editor.close();editor.deleteLater()
  except Exception as e:errors.append([spec.type_id,str(e)])
print(json.dumps(errors,ensure_ascii=False))
raise SystemExit(bool(errors))
