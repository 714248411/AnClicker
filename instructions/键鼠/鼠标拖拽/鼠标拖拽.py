"""鼠标拖拽：独立参数编辑器与执行器。"""

from __future__ import annotations

import math

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.common.mouse_trajectory import TRAJECTORIES, trajectory, screen_bounds
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
        FieldSpec("移动轨迹", "移动轨迹", "choice", "直线", choices=TRAJECTORIES),
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
        if p_.get("录制保持按下"):
            gui_.moveTo(*end_, duration=0, **actions.recording_options(command))
            context.emit(f"录制拖拽：{end_}")
            return (start_, end_)
        duration_ = float(actions.parameter(p_, "移动速度", default=0.5))
        if not math.isfinite(duration_) or not 0 <= duration_ <= 3600:
            raise ValueError("拖拽移动秒数必须在 0 到 3600 之间")
        mode_ = actions.parameter(p_, "移动轨迹", default="直线")
        if mode_ not in TRAJECTORIES:
            raise ValueError(f"未知鼠标移动轨迹：{mode_}")
        if context.stop_requested:
            return None
        gui_.moveTo(*start_, _pause=False)
        if context.stop_requested:
            return None
        held_ = context.metadata.setdefault("recorded_buttons", set())
        held_.add("left")
        try:
            gui_.mouseDown(button="left", _pause=False)
            # Give the target time to recognise the press before moving.  A
            # single dragTo provides neither an explicit hold nor stop checks.
            for _ in range(5):
                if context.stop_requested:
                    return None
                actions.wait_seconds(0.03)
            steps_ = max(1, math.ceil(duration_ / 0.02))
            bounds_ = screen_bounds(gui_, start_, end_) if mode_ != "直线" else None
            for point_ in trajectory(start_, end_, steps_, mode_, bounds=bounds_):
                if context.stop_requested:
                    return None
                gui_.moveTo(*point_, _pause=False)
                actions.wait_seconds(duration_ / steps_)
            if context.stop_requested:
                return None
            actions.wait_seconds(0.05)
        finally:
            # Emergency release must work even if the cursor reached a fail-safe
            # corner. Disable the guard only for release, and always restore it.
            failsafe_ = getattr(gui_, "FAILSAFE", True)
            try:
                gui_.FAILSAFE = False
                gui_.mouseUp(button="left", _pause=False)
                held_.discard("left")
            finally:
                gui_.FAILSAFE = failsafe_
        context.emit(f"鼠标拖拽：{start_} → {end_}")
        return (start_, end_)
