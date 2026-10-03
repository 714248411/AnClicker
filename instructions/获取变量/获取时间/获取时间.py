"""获取时间：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .获取时间_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "获取时间"
    DISPLAY_NAME = "获取时间"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("变量", "变量名称", "text", "当前时间", required=True),
        FieldSpec("时间格式", "时间格式", "choice", "年-月-日 小时:分钟:秒", (
            "年-月-日 小时:分钟:秒",
            "年/月/日 小时:分钟:秒",
            "月/日/年 小时:分钟:秒",
            "日-月-年 小时:分钟:秒",
            "年-月-日",
            "月/日/年",
            "日-月-年",
            "月/年",
            "时间戳",
        ), required=True),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "获取时间"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"获取时间执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        value_ = actions.current_time(str(actions.parameter(command.parameters, "时间格式", default="%Y-%m-%d %H:%M:%S")))
        actions.store_variable(context, command.parameters, value_)
        context.emit(f"获取时间：{value_}")
        return value_
