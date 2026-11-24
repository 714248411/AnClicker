from anclicker.ui.instruction_editors.窗口键鼠.窗口键盘 import InstructionEditor as BaseEditor
from anclicker.instructions.窗口键鼠.窗口按下键盘.schema import FIELDS, OPERATIONS

class InstructionEditor(BaseEditor):
    TYPE_ID = DISPLAY_NAME = '窗口按下键盘'
    DEFAULT_OPERATION = '组合键'
    FIELDS = FIELDS
    OPERATIONS = OPERATIONS
