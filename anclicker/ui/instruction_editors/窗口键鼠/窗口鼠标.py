from anclicker.ui.instruction_editors.窗口键鼠.窗口键鼠 import InstructionEditor as BaseEditor
from anclicker.instructions.窗口键鼠.窗口鼠标.schema import FIELDS, OPERATIONS

class InstructionEditor(BaseEditor):
    TYPE_ID = DISPLAY_NAME = '窗口鼠标'
    FIELDS = FIELDS
    OPERATIONS = OPERATIONS
    DEFAULT_OPERATION = OPERATIONS[0]
