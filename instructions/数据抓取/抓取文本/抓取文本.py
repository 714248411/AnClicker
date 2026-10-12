from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.抓取文本_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '抓取文本'
    DISPLAY_NAME = '抓取文本'
    COMMAND_ID = 'scrapeText'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('selector', '元素定位', 'text', '', choices=(), minimum=0),
        FieldSpec('varName', '保存到变量', 'text', '抓取结果', choices=(), minimum=0),
        FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '文本内容', '智能匹配'), minimum=0),
        FieldSpec('all', '抓取数量', 'choice', '单个', choices=('单个', '全部匹配'), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '抓取文本'
    COMMAND_ID = 'scrapeText'
