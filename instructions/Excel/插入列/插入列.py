from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.插入列_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '插入列'
    DISPLAY_NAME = '插入列'
    COMMAND_ID = 'excelInsertCol'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('col', '在第几列前插入', 'int', 1, choices=(), minimum=1),
        FieldSpec('count', '插入列数', 'int', 1, choices=(), minimum=1),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '插入列'
    COMMAND_ID = 'excelInsertCol'
