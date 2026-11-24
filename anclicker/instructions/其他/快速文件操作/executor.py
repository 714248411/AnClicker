from anclicker.execution.instruction_base import InstructionExecutorBase
from models.system_actions import file_action
class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID='快速文件操作'
    def execute_once(self,context,command):
        if command.type_id!=self.TYPE_ID:raise ValueError('指令类型不匹配')
        p=command.parameters
        return file_action(context,'open' if p['操作']=='打开' else 'copy',p['源路径'],p['目标路径'],p['覆盖'],[x.strip() for x in p['预期文字'].split('|') if x.strip()],p['窗口标题'],p['区域'])
