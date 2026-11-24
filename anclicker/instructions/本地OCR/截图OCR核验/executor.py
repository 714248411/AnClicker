from anclicker.execution.instruction_base import InstructionExecutorBase
from models.screen_verifier import verify_screen
class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID='截图OCR核验'
    def execute_once(self,context,command):
        if command.type_id!=self.TYPE_ID:raise ValueError('指令类型不匹配')
        p=command.parameters
        result=verify_screen(context,[x.strip() for x in p['预期文字'].split('|') if x.strip()],p['窗口标题'],p['区域'],p['识别超时'],p['置信度'])
        context.emit('截图 OCR 核验：'+('通过' if result['verified'] else '未确认')+'；'+result.get('screenshot',''))
        if p['未通过时报错'] and not result['verified']:raise RuntimeError('截图 OCR 核验未通过：'+str(result.get('missing',result.get('error',''))))
        return result
