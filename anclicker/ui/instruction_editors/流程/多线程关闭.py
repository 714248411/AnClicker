from anclicker.ui.instruction_editors.parallel import ParallelEditor
from anclicker.instructions.流程.多线程关闭.schema import FIELDS
from anclicker.instructions.流程.多线程关闭.executor import InstructionExecutor
class InstructionEditor(ParallelEditor):
    TYPE_ID = DISPLAY_NAME = '多线程关闭'
    FIELDS = FIELDS
