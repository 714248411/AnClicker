"""Instruction execution implementation."""
from __future__ import annotations
import random
from anclicker.execution.human_mouse import avoid_failsafe_target
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '移动鼠标'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'移动鼠标执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        gui_ = actions.pyautogui_module()
        type_ = str(actions.parameter(p_, '类型', default='直线移动'))
        from .timing import duration_bounds
        low, high = duration_bounds(actions.parameter(p_, '持续', default='0.5-1.5'))
        duration_ = low if low == high else random.uniform(low, high)
        if type_.startswith(('模拟人1', '模拟人2')):
            from anclicker.execution.human_mouse import move_human
            direction = str(actions.parameter(p_, '方向', default='无'))
            if direction == '无':
                target = actions.point(actions.parameter(p_, '坐标', default='0,0'))
            else:
                distance = int(actions.parameter(p_, '距离', default=100))
                offsets = {'↑':(0,-distance),'↓':(0,distance),'←':(-distance,0),'→':(distance,0)}
                if direction not in offsets: raise ValueError('无效的移动方向')
                sx, sy = gui_.position()
                dx, dy = offsets[direction]
                target = (sx+dx,sy+dy)
            x_, y_ = move_human(gui_, context, target, duration_, 'wind' if type_.startswith('模拟人1') else 'bezier')
        elif type_ == '变量坐标':
            variable_name_ = str(actions.parameter(p_, '变量', default='')).strip()
            if not variable_name_:
                raise ValueError('变量坐标未设置变量名称')
            if variable_name_ not in context.variables:
                raise KeyError(f'变量不存在：{variable_name_}')
            value_ = context.variables[variable_name_]
            if value_ in (None, ''):
                raise ValueError(f'变量坐标为空：{variable_name_}')
            (x_, y_) = actions.point(value_)
            x_, y_ = avoid_failsafe_target(gui_, (x_, y_))
            gui_.moveTo(x_, y_, duration=duration_, **actions.recording_options(command))
        elif type_ == '指定坐标':
            (x_, y_) = actions.point(actions.parameter(p_, '坐标', default='0,0'))
            x_, y_ = avoid_failsafe_target(gui_, (x_, y_))
            gui_.moveTo(x_, y_, duration=duration_, **actions.recording_options(command))
        elif type_ == '随机移动':
            if actions.parameter(p_, '随机', default='类型1') == '类型2':
                distance_ = random.randint(1, 500)
                (dx_, dy_) = random.choice(((0, -distance_), (0, distance_), (-distance_, 0), (distance_, 0)))
                sx_, sy_ = gui_.position()
                width_, height_ = gui_.size()
                target_ = (max(0, min(width_-1, sx_+dx_)), max(0, min(height_-1, sy_+dy_)))
                gui_.moveTo(*avoid_failsafe_target(gui_, target_), duration=duration_)
                (x_, y_) = gui_.position()
            else:
                size_ = gui_.size()
                width_ = size_.width if hasattr(size_, 'width') else size_[0]
                height_ = size_.height if hasattr(size_, 'height') else size_[1]
                (x_, y_) = (random.randint(0, width_ - 1), random.randint(0, height_ - 1))
                x_, y_ = avoid_failsafe_target(gui_, (x_, y_))
                gui_.moveTo(x_, y_, duration=duration_)
        elif str(actions.parameter(p_, '方向', default='→')) == '无':
            x_, y_ = gui_.position()
        else:
            distance_ = int(actions.parameter(p_, '距离', default=100))
            (dx_, dy_) = {'↑': (0, -distance_), '↓': (0, distance_), '←': (-distance_, 0), '→': (distance_, 0)}.get(str(actions.parameter(p_, '方向', default='→')), (distance_, 0))
            sx_, sy_ = gui_.position()
            x_, y_ = avoid_failsafe_target(gui_, (sx_+dx_, sy_+dy_))
            gui_.moveTo(x_, y_, duration=duration_)
            (x_, y_) = gui_.position()
        context.emit(f'移动鼠标：{x_},{y_}')
        return (int(x_), int(y_))
