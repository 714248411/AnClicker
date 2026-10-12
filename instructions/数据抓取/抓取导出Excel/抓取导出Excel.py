from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.抓取导出Excel_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '抓取导出Excel'
    DISPLAY_NAME = '抓取导出Excel'
    COMMAND_ID = 'scrapeExport'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('varName', '数据变量(二维数组)', 'text', '抓取列表', choices=(), minimum=0),
        FieldSpec('path', '保存路径(留空存桌面)', 'text', '', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '抓取导出Excel'
    COMMAND_ID = 'scrapeExport'
