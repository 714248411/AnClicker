"""移动鼠标：独立参数编辑器与执行器。"""

from __future__ import annotations

import random
from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .移动鼠标_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "移动鼠标"
    DISPLAY_NAME = "移动鼠标"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("类型", "移动类型", "choice", "直线移动", ("直线移动", "随机移动", "指定坐标", "变量坐标")),
        FieldSpec("方向", "方向", "choice", "→", ("↑", "↓", "←", "→")),
        FieldSpec("距离", "距离", "int", 100, minimum=0, maximum=100000),
        FieldSpec("随机", "随机方式", "choice", "类型1", ("类型1", "类型2")),
        FieldSpec("坐标", "目标坐标 x,y", "text", "0,0"),
        FieldSpec("持续", "持续秒数", "float", 0.2, minimum=0, maximum=3600),
        FieldSpec("变量", "坐标变量"),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "移动鼠标"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"移动鼠标执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        gui_ = actions.pyautogui_module()
        type_ = str(actions.parameter(p_, "类型", default="直线移动"))
        duration_ = float(actions.parameter(p_, "持续", default=0.2))
        if type_ == "变量坐标":
            variable_name_ = str(actions.parameter(p_, "变量", default="")).strip()
            if not variable_name_:
                raise ValueError("变量坐标未设置变量名称")
            if variable_name_ not in context.variables:
                raise KeyError(f"变量不存在：{variable_name_}")
            value_ = context.variables[variable_name_]
            if value_ in (None, ""):
                raise ValueError(f"变量坐标为空：{variable_name_}")
            x_, y_ = actions.point(value_)
            gui_.moveTo(x_, y_, duration=duration_)
        elif type_ == "指定坐标":
            x_, y_ = actions.point(actions.parameter(p_, "坐标", default="0,0"))
            gui_.moveTo(x_, y_, duration=duration_)
        elif type_ == "随机移动":
            if actions.parameter(p_, "随机", default="类型1") == "类型2":
                distance_ = random.randint(1, 500)
                dx_, dy_ = random.choice(((0, -distance_), (0, distance_), (-distance_, 0), (distance_, 0)))
                gui_.moveRel(dx_, dy_, duration=random.uniform(0.1, 0.9))
                x_, y_ = gui_.position()
            else:
                size_ = gui_.size()
                width_ = size_.width if hasattr(size_, "width") else size_[0]
                height_ = size_.height if hasattr(size_, "height") else size_[1]
                x_, y_ = random.randint(0, width_), random.randint(0, height_)
                gui_.moveTo(x_, y_, duration=random.uniform(0.1, 0.9))
        else:
            distance_ = int(actions.parameter(p_, "距离", default=100))
            dx_, dy_ = {"↑": (0, -distance_), "↓": (0, distance_), "←": (-distance_, 0), "→": (distance_, 0)}.get(
                str(actions.parameter(p_, "方向", default="→")), (distance_, 0)
            )
            gui_.moveRel(dx_, dy_, duration=duration_)
            x_, y_ = gui_.position()
        context.emit(f"移动鼠标：{x_},{y_}")
        return (int(x_), int(y_))
