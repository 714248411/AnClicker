"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'background_runtime_bind_background_etc': ('from', 'anclicker.platform.background_runtime', ('bind_background', 'close_background', 'execute_background_method'), 0),
})


class BackgroundExecutor(InstructionExecutorBase):

    def execute_once(self, context, command):
        if command.type_id != self.TYPE_ID:
            raise ValueError('后台执行器指令类型不匹配')
        (handled, result) = actions.delegated(context, self.TYPE_ID, command)
        if handled:
            return result
        bind_background, close_background, execute_background_method = _module_imports.load('background_runtime_bind_background_etc')
        if self.TYPE_ID == '绑定选择窗口':
            return bind_background(context, command.parameters)
        if self.TYPE_ID == '解除后台绑定':
            close_background(context)
            context.emit('后台绑定已解除，后续普通键鼠指令恢复前台模式')
            return True
        return execute_background_method(context, self.TYPE_ID, command.parameters)
