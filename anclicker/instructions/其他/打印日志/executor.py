"""Write an interpolated message to the existing run log."""
from anclicker.instructions.common import InstructionExecutorBase, actions


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '打印日志'

    def execute_once(self, context, command):
        if command.type_id != self.TYPE_ID:
            raise ValueError('打印日志执行器收到错误的指令类型')
        text = actions.substitute_variables(context, str(command.parameters.get('内容', '')))
        context.emit(text)
        return text
