from anclicker.execution.instruction_base import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '字库点击'
    def execute_once(self, context, command):
        from anclicker.platform.vision_tools.runtime import execute
        if context.stop_requested: return None
        return execute(self.TYPE_ID, command.parameters, context)
