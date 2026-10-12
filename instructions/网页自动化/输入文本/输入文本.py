from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.输入文本_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '输入文本'
    DISPLAY_NAME = '输入文本'
    COMMAND_ID = 'input'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('selector', '元素定位', 'text', '', choices=(), minimum=0),
        FieldSpec('anchor', '锚点元素(可选，多个用;分隔)', 'text', '', choices=(), minimum=0),
        FieldSpec('anchorRel', '目标相对锚点的方位', 'choice', '下方', choices=('下方', '下方第1个', '上方', '右侧', '左侧', '内部', '相邻'), minimum=0),
        FieldSpec('text', '输入内容', 'text', '', choices=(), minimum=0),
        FieldSpec('pressEnter', '输入后按回车', 'choice', '否', choices=('否', '是'), minimum=0),
        FieldSpec('clear', '输入前清空', 'choice', '是', choices=('是', '否'), minimum=0),
        FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '输入文本'
    COMMAND_ID = 'input'
