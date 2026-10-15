"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '坐标点击'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'坐标点击执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        (x_, y_) = actions.point(actions.parameter(command.parameters, '坐标', default='0-0'))
        actions.mouse_action(str(actions.parameter(command.parameters, '动作', default='左键单击')), x_, y_, int(actions.parameter(command.parameters, '自定义次数', default=1)))
        context.emit(f'坐标点击：{x_},{y_}')
        return (x_, y_)
