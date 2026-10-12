from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.删除列_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '删除列'
    DISPLAY_NAME = '删除列'
    COMMAND_ID = 'excelDeleteCol'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('col', '起始列', 'int', 1, choices=(), minimum=1),
        FieldSpec('count', '删除列数', 'int', 1, choices=(), minimum=1),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '删除列'
    COMMAND_ID = 'excelDeleteCol'
