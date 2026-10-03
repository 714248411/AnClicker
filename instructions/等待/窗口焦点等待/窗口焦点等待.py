"""窗口焦点等待：独立参数编辑器与执行器。"""

from __future__ import annotations

import time
from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .窗口焦点等待_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "窗口焦点等待"
    DISPLAY_NAME = "窗口焦点等待"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("标题包含", "窗口标题包含", "text", "", required=True),
        FieldSpec("检测频率", "检测频率", "float", 0.2, minimum=0.01, maximum=60),
        FieldSpec("等待时间", "超时时间", "float", 30, minimum=0, maximum=86400),
        FieldSpec("等待类型", "等待类型", "choice", "获得焦点", ("获得焦点", "失去焦点")),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "窗口焦点等待"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"窗口焦点等待执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        title_ = str(actions.parameter(p_, "标题包含", default=""))
        interval_ = float(actions.parameter(p_, "检测频率", default=0.2))
        deadline_ = time.monotonic() + float(actions.parameter(p_, "等待时间", default=30))
        wait_lost_ = actions.parameter(p_, "等待类型", default="获得焦点") == "失去焦点"
        gui_ = actions.pyautogui_module()
        while time.monotonic() <= deadline_:
            active_ = title_ in str(gui_.getActiveWindowTitle() or "")
            if active_ != wait_lost_:
                context.emit(f"窗口焦点等待完成：{title_}")
                return True
            actions.wait_seconds(interval_)
        raise TimeoutError(f"等待窗口焦点超时：{title_}")
