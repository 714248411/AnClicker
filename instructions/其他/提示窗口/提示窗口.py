"""提示窗口：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .提示窗口_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "提示窗口"
    DISPLAY_NAME = "提示窗口"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("标题", "窗口标题", "text", "提示"),
        FieldSpec("内容", "提示内容", "multiline", ""),
        FieldSpec("图标", "图标", "choice", "信息", ("无", "信息", "警告", "错误", "询问")),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "提示窗口"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"提示窗口执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        import pymsgbox
        icon_ = {
            "无": None,
            "STOP": pymsgbox.STOP,
            "错误": pymsgbox.STOP,
            "WARNING": pymsgbox.WARNING,
            "警告": pymsgbox.WARNING,
            "INFO": pymsgbox.INFO,
            "信息": pymsgbox.INFO,
            "QUESTION": pymsgbox.QUESTION,
            "询问": pymsgbox.QUESTION,
        }.get(str(actions.parameter(command.parameters, "图标", default="信息")))
        pymsgbox.alert(
            text=str(actions.parameter(command.parameters, "内容", default="")),
            title=str(actions.parameter(command.parameters, "标题", default="提示")),
            icon=icon_,
        )
        context.emit("提示窗口已关闭")
        return True
