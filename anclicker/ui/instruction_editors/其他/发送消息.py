from anclicker.instructions.其他.发送消息.schema import FIELDS as InstructionEditor_FIELDS
import sys
from anclicker.instructions.common import FieldSpec, SchemaInstructionEditor, InstructionExecutorBase, actions
from anclicker.ui.generated.instructions.其他.发送消息.发送消息_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.其他.发送消息.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = '发送消息'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS


InstructionExecutor = _module_imports.load('InstructionExecutor')
