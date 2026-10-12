from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.插入行_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '插入行'
    DISPLAY_NAME = '插入行'
    COMMAND_ID = 'excelInsertRow'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('row', '在第几行前插入', 'int', 1, choices=(), minimum=1),
        FieldSpec('count', '插入行数', 'int', 1, choices=(), minimum=1),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '插入行'
    COMMAND_ID = 'excelInsertRow'
