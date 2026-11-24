"""Save the preceding extraction result without variable setup."""
from anclicker.instructions.common import InstructionExecutorBase, actions
from anclicker.platform.extraction_export import export_extracted

class ExportExecutor(InstructionExecutorBase):
    FORMAT = ''
    def execute_once(self, context, command):
        if context.stop_requested:
            raise InterruptedError('已停止导出')
        if 'last_web_extraction' not in context.metadata:
            raise ValueError('请先运行网页提取指令，再运行此转换指令。')
        p = command.parameters
        destination = actions.substitute_variables(context, str(p.get('保存路径', '')))
        result = export_extracted(context.metadata['last_web_extraction'], destination, self.FORMAT, p.get('文件已存在', '自动更名'))
        context.emit('提取结果已保存：' + result)
        return result
