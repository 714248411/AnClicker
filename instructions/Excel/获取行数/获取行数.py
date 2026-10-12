from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.获取行数_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '获取行数'
    DISPLAY_NAME = '获取行数'
    COMMAND_ID = 'excelGetRows'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('varName', '保存到变量', 'text', '行数', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '获取行数'
    COMMAND_ID = 'excelGetRows'
