"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
import math
from anclicker.execution.instruction_helpers.mouse_trajectory import screen_bounds
from anclicker.execution.instruction_helpers.mouse_trajectory import trajectory
from anclicker.execution.instruction_helpers.mouse_trajectory import TRAJECTORIES
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '鼠标拖拽'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'鼠标拖拽执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        start_ = actions.point(actions.parameter(p_, '开始位置', default='0,0'))
        end_ = actions.point(actions.parameter(p_, '结束位置', default='0,0'))
        (sdx_, sdy_) = actions.random_offset(bool(actions.parameter(p_, '开始随机', default=False)))
        (edx_, edy_) = actions.random_offset(bool(actions.parameter(p_, '结束随机', default=False)))
        start_ = (start_[0] + sdx_, start_[1] + sdy_)
        end_ = (end_[0] + edx_, end_[1] + edy_)
        gui_ = actions.pyautogui_module()
        if p_.get('录制保持按下'):
            gui_.moveTo(*end_, duration=0, **actions.recording_options(command))
            context.emit(f'录制拖拽：{end_}')
            return (start_, end_)
        duration_ = float(actions.parameter(p_, '移动速度', default=0.5))
        if not math.isfinite(duration_) or not 0 <= duration_ <= 3600:
            raise ValueError('拖拽移动秒数必须在 0 到 3600 之间')
        mode_ = actions.parameter(p_, '移动轨迹', default='直线')
        if mode_ not in TRAJECTORIES:
            raise ValueError(f'未知鼠标移动轨迹：{mode_}')
        if context.stop_requested:
            return None
        gui_.moveTo(*start_, _pause=False)
        if context.stop_requested:
            return None
        held_ = context.metadata.setdefault('recorded_buttons', set())
        held_.add('left')
        try:
            gui_.mouseDown(button='left', _pause=False)
            for _ in range(5):
                if context.stop_requested:
                    return None
                actions.wait_seconds(0.03)
            steps_ = max(1, math.ceil(duration_ / 0.02))
            bounds_ = screen_bounds(gui_, start_, end_) if mode_ != '直线' else None
            for point_ in trajectory(start_, end_, steps_, mode_, bounds=bounds_):
                if context.stop_requested:
                    return None
                gui_.moveTo(*point_, _pause=False)
                actions.wait_seconds(duration_ / steps_)
            if context.stop_requested:
                return None
            actions.wait_seconds(0.05)
        finally:
            failsafe_ = getattr(gui_, 'FAILSAFE', True)
            try:
                gui_.FAILSAFE = False
                gui_.mouseUp(button='left', _pause=False)
                held_.discard('left')
            finally:
                gui_.FAILSAFE = failsafe_
        context.emit(f'鼠标拖拽：{start_} → {end_}')
        return (start_, end_)
