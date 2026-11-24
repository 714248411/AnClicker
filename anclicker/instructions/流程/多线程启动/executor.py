from anclicker.execution.instruction_base import InstructionExecutorBase
class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '多线程启动'
    def execute_once(self, context, command):
        from anclicker.execution.parallel_runtime import execute
        if not context.stop_requested:
            return execute(self.TYPE_ID, command.parameters, context)
