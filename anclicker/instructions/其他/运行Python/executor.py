"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '运行Python'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'运行Python执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        return_value_ = actions.parameter(p_, '返回值', default='')
        if isinstance(return_value_, bool):
            result_name_ = 'result' if return_value_ else ''
            variable_name_ = str(actions.parameter(p_, '变量', default='')) if return_value_ else ''
        else:
            result_name_ = str(return_value_ or '').strip()
            variable_name_ = str(actions.parameter(p_, '变量', default='')).strip() if result_name_ else ''
        result_ = actions.run_python_code(context, str(actions.parameter(p_, '代码', '内容', default='')), result_name_, variable_name_)
        context.emit('运行Python完成')
        return result_
