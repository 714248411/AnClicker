"""获取鼠标位置：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .获取鼠标位置_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "获取鼠标位置"
    DISPLAY_NAME = "获取鼠标位置"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("变量", "变量名称", "text", "鼠标位置", required=True),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "获取鼠标位置"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"获取鼠标位置执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        position_ = actions.pyautogui_module().position()
        value_ = [int(position_.x), int(position_.y)]
        actions.store_variable(context, command.parameters, value_)
        context.emit(f"获取鼠标位置：{value_}")
        return value_
