"""滚轮滑动：独立参数编辑器与执行器。"""

from __future__ import annotations

import random
from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .滚轮滑动_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "滚轮滑动"
    DISPLAY_NAME = "滚轮滑动"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("类型", "滑动类型", "choice", "滚轮滑动", ("滚轮滑动", "随机滚轮滑动")),
        FieldSpec("方向", "方向", "choice", "向下", ("向上", "向下")),
        FieldSpec("距离", "距离", "int", 5, minimum=1, maximum=100000),
        FieldSpec("最小距离", "随机最小距离", "int", 1, minimum=1, maximum=100000),
        FieldSpec("最大距离", "随机最大距离", "int", 10, minimum=1, maximum=100000),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "滚轮滑动"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"滚轮滑动执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        if actions.parameter(p_, "类型", default="滚轮滑动") == "随机滚轮滑动":
            distance_ = random.randint(int(actions.parameter(p_, "最小距离", default=1)), int(actions.parameter(p_, "最大距离", default=10)))
        else:
            distance_ = int(actions.parameter(p_, "距离", default=5))
        if actions.parameter(p_, "方向", default="向下") == "向下":
            distance_ = -distance_
        actions.pyautogui_module().scroll(distance_)
        context.emit(f"滚轮滑动：{distance_}")
        return distance_
