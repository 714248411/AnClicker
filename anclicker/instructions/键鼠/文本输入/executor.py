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
    TYPE_ID = '文本输入'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'文本输入执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        text_ = actions.substitute_variables(context, str(actions.parameter(command.parameters, '内容', '文本', default='')))
        gui_ = actions.pyautogui_module()
        if getattr(gui_, 'is_background', False) is True or actions.parameter(command.parameters, '手动输入', default=False):
            gui_.write(text_)
        else:
            pyperclip = _module_imports.load('pyperclip')
            pyperclip.copy(text_)
            gui_.hotkey('ctrl', 'v')
        context.emit(f'文本输入：{text_}')
        return text_
