from anclicker.domain.instruction_interfaces import InstructionExecutorInterface

class InstructionExecutor(InstructionExecutorInterface):
    TYPE_ID = '折叠步骤'

    def execute(self, context, command):
        # Presentation metadata must never skip, delay or execute child commands.
        return None
