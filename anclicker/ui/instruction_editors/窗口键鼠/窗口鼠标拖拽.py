from anclicker.ui.instruction_editors.窗口键鼠.窗口键鼠 import InstructionEditor as BaseEditor
from anclicker.instructions.窗口键鼠.窗口鼠标拖拽.schema import FIELDS, OPERATIONS

class InstructionEditor(BaseEditor):
    TYPE_ID = DISPLAY_NAME = '窗口鼠标拖拽'
    DEFAULT_OPERATION = '鼠标拖拽'
    FIELDS = FIELDS
    OPERATIONS = OPERATIONS
