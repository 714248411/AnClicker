"""坐标点击：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .坐标点击_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "坐标点击"
    DISPLAY_NAME = "坐标点击"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("动作", "鼠标动作", "choice", "左键单击", ("左键单击", "左键双击", "右键单击", "右键双击", "左键（自定义次数）", "仅移动鼠标")),
        FieldSpec("坐标", "坐标 x-y", "text", "0-0", required=True),
        FieldSpec("自定义次数", "点击次数", "int", 1, minimum=1, maximum=9999),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "坐标点击"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"坐标点击执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        x_, y_ = actions.point(actions.parameter(command.parameters, "坐标", default="0-0"))
        actions.mouse_action(
            str(actions.parameter(command.parameters, "动作", default="左键单击")),
            x_, y_, int(actions.parameter(command.parameters, "自定义次数", default=1)),
        )
        context.emit(f"坐标点击：{x_},{y_}")
        return (x_, y_)
