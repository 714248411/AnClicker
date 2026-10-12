from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.删除行_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '删除行'
    DISPLAY_NAME = '删除行'
    COMMAND_ID = 'excelDeleteRow'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('row', '起始行', 'int', 1, choices=(), minimum=1),
        FieldSpec('count', '删除行数', 'int', 1, choices=(), minimum=1),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '删除行'
    COMMAND_ID = 'excelDeleteRow'
