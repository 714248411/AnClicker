import sys
from instructions.common import FieldSpec, SchemaInstructionEditor, InstructionExecutorBase, actions
from .发送消息_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = '发送消息'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('联系人', '微信联系人（精确名称）', 'text', '', required=True),
        FieldSpec('消息内容', '消息内容', 'multiline', '', required=True),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '发送消息'
    CONSUMED_FIELDS = ('联系人', '消息内容')

    def execute_once(self, context, command):
        handled, result = actions.delegated(context, self.TYPE_ID, command)
        if handled:
            return result
        if context.stop_requested:
            return
        if sys.platform != 'win32':
            raise RuntimeError('微信消息自动化只支持 Windows；联系人与消息内容已保留，未发送。')
        try:
            from wxauto import WeChat
        except ImportError as error:
            raise RuntimeError('微信消息需要兼容的 wxauto 和微信客户端；当前环境未安装，未发送。') from error
        who = actions.substitute_variables(context, str(command.parameters.get('联系人', ''))).strip()
        message = actions.substitute_variables(context, str(command.parameters.get('消息内容', '')))
        if not who or not message:
            raise ValueError('微信联系人与消息内容不能为空')
        client = WeChat()
        # Never accept a fuzzy search result: it could send private data to someone else.
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
