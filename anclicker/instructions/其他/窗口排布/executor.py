"""Arrange a saved selection of application windows."""
from anclicker.instructions.common import InstructionExecutorBase,actions
from anclicker.platform.window_arrangement import apply_arrangement

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID='窗口排布'
    def execute_once(self,context,command):
        delegated,result=actions.delegated(context,self.TYPE_ID,command)
        if delegated:return result
        if command.type_id!=self.TYPE_ID:raise ValueError('窗口排布执行器收到其他指令')
        results=apply_arrangement(command.parameters,context)
        context.set_variable('窗口排布结果',results)
        limited=sum(bool(item['系统限制']) for item in results)
        context.emit('已排布 '+str(len(results))+' 个窗口'+('；其中 '+str(limited)+' 个受程序最小尺寸等限制' if limited else ''))
        return results
