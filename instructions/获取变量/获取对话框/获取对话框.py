"""获取对话框：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .获取对话框_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "获取对话框"
    DISPLAY_NAME = "获取对话框"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("标题", "对话框标题", "text", "请输入"),
        FieldSpec("变量", "变量名称", "text", "输入值", required=True),
        FieldSpec("提示", "提示内容", "multiline", "请输入内容"),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "获取对话框"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"获取对话框执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        import pymsgbox
        value_ = pymsgbox.prompt(
            text=str(actions.parameter(command.parameters, "提示", default="请输入内容")),
            title=str(actions.parameter(command.parameters, "标题", default="请输入")),
        )
        actions.store_variable(context, command.parameters, value_)
        context.emit("已获取对话框输入")
        return value_
