from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.打开Excel_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '打开Excel'
    DISPLAY_NAME = '打开Excel'
    COMMAND_ID = 'excelOpen'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('path', '文件路径', 'text', '', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '打开Excel'
    COMMAND_ID = 'excelOpen'
