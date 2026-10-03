"""图像等待：独立参数编辑器与执行器。"""

from __future__ import annotations

import time
from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .图像等待_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "图像等待"
    DISPLAY_NAME = "图像等待"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("图像路径", "图像路径", "path", "", required=True),
        FieldSpec("等待类型", "等待类型", "choice", "等待出现", ("等待出现", "等待消失")),
        FieldSpec("超时时间", "超时时间", "float", 10, minimum=0, maximum=86400),
        FieldSpec("区域", "识别区域 x,y,w,h"),
        FieldSpec("精度", "识别精度", "float", 0.8, minimum=0.01, maximum=1.0),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "图像等待"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"图像等待执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        timeout_ = float(actions.parameter(p_, "超时时间", default=10))
        wait_disappear_ = actions.parameter(p_, "等待类型", default="等待出现") == "等待消失"
        deadline_ = time.monotonic() + timeout_
        while True:
            found_ = actions.locate_image(p_, context) is not None
            if found_ != wait_disappear_:
                context.emit("图像等待完成")
                return found_
            if time.monotonic() >= deadline_:
                raise TimeoutError("图像等待超时")
            actions.wait_seconds(0.1)
