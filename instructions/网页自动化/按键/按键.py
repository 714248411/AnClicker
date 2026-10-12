from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.按键_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '按键'
    DISPLAY_NAME = '按键'
    COMMAND_ID = 'pressKey'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('key', '按哪个键', 'choice', '回车(Enter)', choices=('回车(Enter)', 'Tab', 'ESC(Esc)', '空格(Space)', '退格(Backspace)', '删除(Delete)', '方向键↑', '方向键↓', '方向键←', '方向键→', 'F5(刷新页面)', 'Ctrl+A(全选)', 'Ctrl+C(复制)', 'Ctrl+V(粘贴)', 'Ctrl+X(剪切)', 'Ctrl+Z(撤销)', 'Ctrl+F(查找)', 'Ctrl+S(保存)', '自定义'), minimum=0),
        FieldSpec('customKey', '自定义按键(选「自定义」时填，如 F5、a、Ctrl+Shift+A)', 'text', '', choices=(), minimum=0),
        FieldSpec('times', '按几次', 'int', 1, choices=(), minimum=1),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '按键'
    COMMAND_ID = 'pressKey'
