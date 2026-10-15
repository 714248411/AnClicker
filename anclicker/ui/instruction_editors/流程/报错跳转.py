from anclicker.instructions.流程.报错跳转.schema import FIELDS as InstructionEditor_FIELDS
from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, actions
from anclicker.ui.instruction_editors.flow_jump_editor import JumpEditor
from anclicker.domain.flow_jumps import TARGET_MODES
from anclicker.ui.generated.instructions.流程.报错跳转.报错跳转_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.流程.报错跳转.executor', ('InstructionExecutor',), 0),
})


class InstructionEditor(JumpEditor):
    TYPE_ID = DISPLAY_NAME = '报错跳转'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

InstructionExecutor = _module_imports.load('InstructionExecutor')
