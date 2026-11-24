"""Instruction execution implementation."""
from __future__ import annotations
import json
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'pymsgbox': ('import', 'pymsgbox', (), False),
})


def message_text(context, parameters):
    content = actions.substitute_variables(context, str(parameters.get('内容', '')))
    name = str(parameters.get('变量') or '').strip()
    if not name:
        return content
    if name not in context.variables:
        raise ValueError('提示窗口所选变量不存在：' + name)
    value = context.variables[name]
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    else:
        value = '' if value is None else str(value)
    order = parameters.get('显示顺序', '提示内容在前')
    if order not in ('提示内容在前', '变量值在前'):
        raise ValueError('提示窗口显示顺序无效')
    return value + content if order == '变量值在前' else content + value


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '提示窗口'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'提示窗口执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        text = message_text(context, command.parameters)
        pymsgbox = _module_imports.load('pymsgbox')
        icon_ = {'无': None, 'STOP': pymsgbox.STOP, '错误': pymsgbox.STOP, 'WARNING': pymsgbox.WARNING, '警告': pymsgbox.WARNING, 'INFO': pymsgbox.INFO, '信息': pymsgbox.INFO, 'QUESTION': pymsgbox.QUESTION, '询问': pymsgbox.QUESTION}.get(str(actions.parameter(command.parameters, '图标', default='信息')))
        pymsgbox.alert(text=text, title=str(actions.parameter(command.parameters, '标题', default='提示')), icon=icon_)
        context.emit('提示窗口已关闭')
        return True
