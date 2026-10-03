"""鼠标拖拽：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .鼠标拖拽_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "鼠标拖拽"
    DISPLAY_NAME = "鼠标拖拽"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("开始位置", "开始位置 x,y", "text", "0,0", required=True),
        FieldSpec("结束位置", "结束位置 x,y", "text", "0,0", required=True),
        FieldSpec("开始随机", "开始位置随机偏移", "bool", False),
        FieldSpec("结束随机", "结束位置随机偏移", "bool", False),
        FieldSpec("移动速度", "移动秒数", "float", 0.5, minimum=0, maximum=3600),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "鼠标拖拽"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"鼠标拖拽执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        start_ = actions.point(actions.parameter(p_, "开始位置", default="0,0"))
        end_ = actions.point(actions.parameter(p_, "结束位置", default="0,0"))
        sdx_, sdy_ = actions.random_offset(bool(actions.parameter(p_, "开始随机", default=False)))
        edx_, edy_ = actions.random_offset(bool(actions.parameter(p_, "结束随机", default=False)))
        start_ = (start_[0] + sdx_, start_[1] + sdy_)
        end_ = (end_[0] + edx_, end_[1] + edy_)
        gui_ = actions.pyautogui_module()
        gui_.moveTo(*start_)
        gui_.dragTo(*end_, duration=float(actions.parameter(p_, "移动速度", default=0.5)), button="left")
        context.emit(f"鼠标拖拽：{start_} → {end_}")
        return (start_, end_)
