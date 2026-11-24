from anclicker.instructions.窗口键鼠.窗口键鼠.executor import InstructionExecutor as BaseExecutor
from .schema import OPERATIONS

class InstructionExecutor(BaseExecutor):
    TYPE_ID = '窗口鼠标'
    DEFAULT_OPERATION = OPERATIONS[0]

    def execute_once(self, context, command):
        if command.parameters.get('操作', OPERATIONS[0]) not in OPERATIONS:
            raise ValueError('该操作不属于窗口鼠标')
        return super().execute_once(context, command)
