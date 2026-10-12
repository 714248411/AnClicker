from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.复制到剪贴板_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '复制到剪贴板'
    DISPLAY_NAME = '复制到剪贴板'
    COMMAND_ID = 'clipboardCopy'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('from', '复制什么', 'choice', '文本(下面填的内容)', choices=('文本(下面填的内容)', '网页里选中的内容', '元素里的文本'), minimum=0),
        FieldSpec('content', '要复制的文本(可用 ${变量})', 'text', '', choices=(), minimum=0),
        FieldSpec('selector', '元素定位(上面选「元素里的文本」时填)', 'text', '', choices=(), minimum=0),
        FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '文本内容', '智能匹配'), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '复制到剪贴板'
    COMMAND_ID = 'clipboardCopy'
