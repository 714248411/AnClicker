from anclicker.execution.instruction_base import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '小地图拼接制作大地图'
    def execute_once(self, context, command):
        from anclicker.platform.vision_tools.runtime import execute
        if context.stop_requested: return None
        return execute(self.TYPE_ID, command.parameters, context)
