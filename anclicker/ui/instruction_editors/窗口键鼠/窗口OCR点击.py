from anclicker.ui.instruction_editors.window_operation_editor import WindowOperationEditor
from anclicker.instructions.窗口键鼠.窗口OCR点击.schema import FIELDS, OPERATIONS, EXTRA_FIELDS

class InstructionEditor(WindowOperationEditor):
    TYPE_ID = DISPLAY_NAME = '窗口OCR点击'
    FIELDS = FIELDS
    OPERATIONS = OPERATIONS
    EXTRA_FIELDS = EXTRA_FIELDS
