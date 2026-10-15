"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '获取Excel'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'获取Excel执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        cell_ = actions.resolve_increment(str(actions.parameter(p_, '单元格', default='A1')), bool(actions.parameter(p_, '递增', default=False)), context.iteration)
        (workbook_, _, cell_object_) = actions.workbook_cell(str(actions.parameter(p_, '工作簿', default='')), str(actions.parameter(p_, '工作表', default='')), cell_)
        try:
            value_ = cell_object_.value
        finally:
            workbook_.close()
        actions.store_variable(context, p_, value_)
        context.emit(f'获取Excel：{cell_}={value_}')
        return value_
