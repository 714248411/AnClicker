"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
import sys
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'window_backend_': ('import', 'pygetwindow', (), True),
    'window_backend__2': ('import', 'pywinctl', (), True),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '窗口控制'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'窗口控制执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        if sys.platform == 'win32':
            window_backend_ = _module_imports.load('window_backend_')
        else:
            window_backend_ = _module_imports.load('window_backend__2')
        p_ = command.parameters
        title_ = str(actions.parameter(p_, '标题包含', default=''))
        windows_ = window_backend_.getWindowsWithTitle(title_)
        if not windows_:
            if actions.parameter(p_, '报错', default=True):
                raise RuntimeError(f'未找到窗口：{title_}')
            return False
        window_ = windows_[0]
        operation_ = str(actions.parameter(p_, '操作', default='激活'))
        method_ = {'激活': 'activate', '最小化': 'minimize', '最大化': 'maximize', '还原': 'restore', '关闭': 'close'}[operation_]
        getattr(window_, method_)()
        context.emit(f'窗口控制：{operation_}')
        return True
