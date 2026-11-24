from anclicker.instructions.common import InstructionExecutorBase
from anclicker.execution.instruction_helpers.window_trigger_wait import wait_for_trigger

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '窗口中键激活'

    def execute_once(self, context, command):
        if command.type_id != self.TYPE_ID:
            raise ValueError('触发等待指令类型不匹配')
        triggered = wait_for_trigger(context, command.parameters)
        context.emit('触发按键已按下，继续下一步' if triggered else '触发等待已取消')
        return triggered
