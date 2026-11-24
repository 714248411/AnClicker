from anclicker.ui.instruction_editors.窗口键鼠.窗口键鼠 import InstructionEditor as BaseEditor
from anclicker.instructions.窗口键鼠.窗口滚轮滑动.schema import FIELDS, OPERATIONS

class InstructionEditor(BaseEditor):
    TYPE_ID = DISPLAY_NAME = '窗口滚轮滑动'
    DEFAULT_OPERATION = '滚轮滑动'
    FIELDS = FIELDS
    OPERATIONS = OPERATIONS
