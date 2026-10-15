"""窗口焦点等待：独立参数编辑器与执行器。"""

from __future__ import annotations
from anclicker.instructions.等待.窗口焦点等待.schema import FIELDS as InstructionEditor_FIELDS

import time
from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.ui.generated.instructions.等待.窗口焦点等待.窗口焦点等待_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.等待.窗口焦点等待.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "窗口焦点等待"
    DISPLAY_NAME = "窗口焦点等待"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS


InstructionExecutor = _module_imports.load('InstructionExecutor')
