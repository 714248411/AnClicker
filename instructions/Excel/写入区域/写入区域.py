from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.写入区域_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '写入区域'
    DISPLAY_NAME = '写入区域'
    COMMAND_ID = 'excelWriteRange'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('range', '起始单元格(如A1)', 'text', 'A1', choices=(), minimum=0),
        FieldSpec('data', '数据(变量名,二维数组)', 'text', '变量1', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '写入区域'
    COMMAND_ID = 'excelWriteRange'
