from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.点击元素_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '点击元素'
    DISPLAY_NAME = '点击元素'
    COMMAND_ID = 'click'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('selector', '元素定位', 'text', '', choices=(), minimum=0),
        FieldSpec('anchor', '锚点元素(可选，多个用;分隔)', 'text', '', choices=(), minimum=0),
        FieldSpec('anchorRel', '目标相对锚点的方位', 'choice', '下方', choices=('下方', '上方', '右侧', '左侧', '内部', '相邻'), minimum=0),
        FieldSpec('clickType', '点击方式', 'choice', '单击', choices=('单击', '双击', '右键'), minimum=0),
        FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '文本内容', '坐标定位', '智能匹配', '锚点定位'), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '点击元素'
    COMMAND_ID = 'click'
