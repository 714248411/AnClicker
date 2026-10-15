"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '终止流程'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'终止流程执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        context.stop_requested = True
        context.emit(str(actions.parameter(command.parameters, '终止类型', default='终止所有任务')))
        return True
