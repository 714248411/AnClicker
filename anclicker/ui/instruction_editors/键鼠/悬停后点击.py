from anclicker.instructions.键鼠.悬停后点击.schema import FIELDS as InstructionEditor_FIELDS
"""展开悬停菜单，缓慢移动至目标，然后点击。"""
import math

from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor, actions
from anclicker.execution.instruction_helpers.mouse_trajectory import trajectory, wait_interruptibly
from anclicker.ui.generated.instructions.键鼠.悬停后点击.悬停后点击_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.键鼠.悬停后点击.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = "悬停后点击"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS


InstructionExecutor = _module_imports.load('InstructionExecutor')
