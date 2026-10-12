from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.新建Excel_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '新建Excel'
    DISPLAY_NAME = '新建Excel'
    COMMAND_ID = 'excelNew'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('path', '保存路径', 'text', '', choices=(), minimum=0),
        FieldSpec('sheetName', '工作表名', 'text', 'Sheet1', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '新建Excel'
    COMMAND_ID = 'excelNew'
