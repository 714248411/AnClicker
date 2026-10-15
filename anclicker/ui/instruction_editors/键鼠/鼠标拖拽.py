"""鼠标拖拽：独立参数编辑器与执行器。"""

from __future__ import annotations
from anclicker.instructions.键鼠.鼠标拖拽.schema import FIELDS as InstructionEditor_FIELDS

import math

from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.execution.instruction_helpers.mouse_trajectory import TRAJECTORIES, trajectory, screen_bounds
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.ui.generated.instructions.键鼠.鼠标拖拽.鼠标拖拽_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.键鼠.鼠标拖拽.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "鼠标拖拽"
    DISPLAY_NAME = "鼠标拖拽"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS


InstructionExecutor = _module_imports.load('InstructionExecutor')
