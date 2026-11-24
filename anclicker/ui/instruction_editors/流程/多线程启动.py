from anclicker.ui.instruction_editors.parallel import ParallelEditor
from anclicker.instructions.流程.多线程启动.schema import FIELDS
from anclicker.instructions.流程.多线程启动.executor import InstructionExecutor
class InstructionEditor(ParallelEditor):
    TYPE_ID = DISPLAY_NAME = '多线程启动'
    FIELDS = FIELDS
