from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.读取区域_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '读取区域'
    DISPLAY_NAME = '读取区域'
    COMMAND_ID = 'excelReadRange'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('range', '区域(如A1:C5)', 'text', 'A1:C5', choices=(), minimum=0),
        FieldSpec('varName', '保存到变量(二维数组)', 'text', '变量1', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '读取区域'
    COMMAND_ID = 'excelReadRange'
