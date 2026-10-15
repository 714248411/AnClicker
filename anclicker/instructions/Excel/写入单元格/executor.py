"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '写入单元格'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'写入单元格执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        path_ = str(actions.parameter(p_, '工作簿', default=''))
        cell_ = actions.resolve_increment(str(actions.parameter(p_, '单元格', default='A1')), bool(actions.parameter(p_, '递增', default=False)), context.iteration)
        (workbook_, _, cell_object_) = actions.workbook_cell(path_, str(actions.parameter(p_, '工作表', default='')), cell_, data_only=False)
        try:
            value_ = actions.substitute_variables(context, str(actions.parameter(p_, '文本', default='')))
            cell_object_.value = value_
            workbook_.save(path_)
        finally:
            workbook_.close()
        context.emit(f'写入单元格：{cell_}')
        return value_
