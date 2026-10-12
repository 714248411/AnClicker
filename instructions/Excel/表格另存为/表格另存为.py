from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.表格另存为_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '表格另存为'
    DISPLAY_NAME = '表格另存为'
    COMMAND_ID = 'excelSaveAs'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('naming', '命名方式', 'choice', '后缀递增', choices=('后缀递增', '加前缀', '覆盖'), minimum=0),
        FieldSpec('prefix', '前缀(选「加前缀」时用)', 'text', '', choices=(), minimum=0),
        FieldSpec('startIndex', '后缀从几开始(默认1)', 'int', 1, choices=(), minimum=1),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '表格另存为'
    COMMAND_ID = 'excelSaveAs'
