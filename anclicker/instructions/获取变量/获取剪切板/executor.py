"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'pyperclip': ('import', 'pyperclip', (), False),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '获取剪切板'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'获取剪切板执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        pyperclip = _module_imports.load('pyperclip')
        value_ = pyperclip.paste()
        actions.store_variable(context, command.parameters, value_)
        context.emit('已获取剪切板')
        return value_
