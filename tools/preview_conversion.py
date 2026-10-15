import os,sys
from pathlib import Path

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
    'QApplication': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QApplication',), 0),
    'prepare_instruction_conversion': ('from', 'anclicker.domain.instruction_code', ('prepare_instruction_conversion',), 0),
    'InstructionConversionDialog': ('from', 'anclicker.ui.instruction_conversion_dialog', ('InstructionConversionDialog',), 0),
})

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
anclicker = _module_imports.load('anclicker')  # Enable source-tree legacy entry points.
os.environ['QT_QPA_PLATFORM']='windows'
QApplication = _module_imports.load('QApplication')
prepare_instruction_conversion = _module_imports.load('prepare_instruction_conversion')
InstructionConversionDialog = _module_imports.load('InstructionConversionDialog')
app=QApplication([])
dialog=InstructionConversionDialog(prepare_instruction_conversion('时间等待({"时长":\n打开网页({"url": "https://www.hao123.com"})'))
dialog.show();app.processEvents()
dialog.grab().save('artifacts/validation/conversion-dialog.png')
dialog.close()
