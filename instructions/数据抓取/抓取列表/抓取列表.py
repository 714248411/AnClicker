from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.抓取列表_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '抓取列表'
    DISPLAY_NAME = '抓取列表'
    COMMAND_ID = 'scrapeList'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('selector', '列表项定位', 'text', '', choices=(), minimum=0),
        FieldSpec('fields', '字段(定位:字段名,逗号分隔)', 'text', '', choices=(), minimum=0),
        FieldSpec('varName', '保存到变量(二维数组)', 'text', '抓取列表', choices=(), minimum=0),
        FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '智能匹配'), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '抓取列表'
    COMMAND_ID = 'scrapeList'
