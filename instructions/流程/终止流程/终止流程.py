"""终止流程：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .终止流程_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "终止流程"
    DISPLAY_NAME = "终止流程"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("终止类型", "终止类型", "choice", "终止所有任务", ("终止所有任务",)),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "终止流程"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"终止流程执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        context.stop_requested = True
        context.emit(str(actions.parameter(command.parameters, "终止类型", default="终止所有任务")))
        return True
