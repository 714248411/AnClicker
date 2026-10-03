"""获取剪切板：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .获取剪切板_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "获取剪切板"
    DISPLAY_NAME = "获取剪切板"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("变量", "变量名称", "text", "剪切板", required=True),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "获取剪切板"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"获取剪切板执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        import pyperclip

        value_ = pyperclip.paste()
        actions.store_variable(context, command.parameters, value_)
        context.emit("已获取剪切板")
        return value_
