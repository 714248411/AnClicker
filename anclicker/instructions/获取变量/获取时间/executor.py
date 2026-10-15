"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '获取时间'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'获取时间执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        value_ = actions.current_time(str(actions.parameter(command.parameters, '时间格式', default='%Y-%m-%d %H:%M:%S')))
        actions.store_variable(context, command.parameters, value_)
        context.emit(f'获取时间：{value_}')
        return value_
