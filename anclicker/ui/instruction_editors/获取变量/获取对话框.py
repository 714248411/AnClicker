"""获取对话框：独立参数编辑器与执行器。"""

from __future__ import annotations
from anclicker.instructions.获取变量.获取对话框.schema import FIELDS as InstructionEditor_FIELDS

from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.ui.generated.instructions.获取变量.获取对话框.获取对话框_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.获取变量.获取对话框.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "获取对话框"
    DISPLAY_NAME = "获取对话框"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS


InstructionExecutor = _module_imports.load('InstructionExecutor')
