from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.抓取属性_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '抓取属性'
    DISPLAY_NAME = '抓取属性'
    COMMAND_ID = 'scrapeAttr'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('selector', '元素定位', 'text', '', choices=(), minimum=0),
        FieldSpec('attr', '属性名(如href)', 'text', 'href', choices=(), minimum=0),
        FieldSpec('varName', '保存到变量', 'text', '抓取结果', choices=(), minimum=0),
        FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '智能匹配'), minimum=0),
        FieldSpec('all', '抓取数量', 'choice', '全部匹配', choices=('单个', '全部匹配'), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '抓取属性'
    COMMAND_ID = 'scrapeAttr'
