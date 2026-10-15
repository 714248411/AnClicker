"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.flow_jumps import compare_variables
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '变量比较'
    CONSUMED_FIELDS = ('变量', '比较条件', '比较对象', '比较值', '比较类型', '是跳转方式', '是目标行', '是项目路径', '否跳转方式', '否目标行', '否项目路径')

    def execute_once(self, context, command):
        (handled, result) = actions.delegated(context, self.TYPE_ID, command)
        if handled:
            return result
        result = compare_variables(command.parameters, context.variables)
        context.emit('变量比较结果：' + ('是' if result else '否'))
        return result
