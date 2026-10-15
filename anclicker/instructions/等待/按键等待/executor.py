"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'wait_for_key': ('from', 'anclicker.execution.instruction_helpers.key_wait', ('wait_for_key',), 0),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '按键等待'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'按键等待执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        wait_type_ = str(actions.parameter(command.parameters, '等待类型', default='按键等待'))
        if wait_type_ != '按键等待':
            raise ValueError(f'不支持的按键等待类型：{wait_type_}')
        key_ = str(actions.parameter(command.parameters, '按键', default='enter'))
        wait_for_key = _module_imports.load('wait_for_key')
        if not wait_for_key(context, key_):
            return None
        context.emit(f'检测到按键：{key_}')
        return key_
