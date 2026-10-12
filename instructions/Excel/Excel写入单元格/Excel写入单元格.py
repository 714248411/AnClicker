from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.Excel写入单元格_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = 'Excel写入单元格'
    DISPLAY_NAME = '写入单元格'
    COMMAND_ID = 'excelWrite'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('cell', '单元格(如A1)', 'text', 'A1', choices=(), minimum=0),
        FieldSpec('value', '写入内容', 'text', '', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = 'Excel写入单元格'
    COMMAND_ID = 'excelWrite'
