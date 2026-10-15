"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
import sys
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'WeChat': ('from', 'wxauto', ('WeChat',), 0),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '发送消息'
    CONSUMED_FIELDS = ('联系人', '消息内容')

    def execute_once(self, context, command):
        (handled, result) = actions.delegated(context, self.TYPE_ID, command)
        if handled:
            return result
        if context.stop_requested:
            return
        if sys.platform != 'win32':
            raise RuntimeError('微信消息自动化只支持 Windows；联系人与消息内容已保留，未发送。')
        try:
            WeChat = _module_imports.load('WeChat')
        except ImportError as error:
            raise RuntimeError('微信消息需要兼容的 wxauto 和微信客户端；当前环境未安装，未发送。') from error
        who = actions.substitute_variables(context, str(command.parameters.get('联系人', ''))).strip()
        message = actions.substitute_variables(context, str(command.parameters.get('消息内容', '')))
        if not who or not message:
            raise ValueError('微信联系人与消息内容不能为空')
        client = WeChat()
        selected = client.ChatWith(who)
        if selected != who:
            raise RuntimeError('未找到精确匹配的微信联系人，已取消发送。')
        if context.stop_requested:
            return
        result = client.SendMsg(msg=message, who=who)
        if result is False:
            raise RuntimeError('微信客户端报告消息发送失败')
        context.emit('微信消息发送操作完成')
        return result
