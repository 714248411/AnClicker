from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.复制粘贴（选择性粘贴）_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '复制粘贴（选择性粘贴）'
    DISPLAY_NAME = '复制粘贴(选择性粘贴)'
    COMMAND_ID = 'excelCopyPaste'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('from', '源区域(如A1:B5)', 'text', 'A1:B5', choices=(), minimum=0),
        FieldSpec('to', '目标起始单元格(如D1)', 'text', 'D1', choices=(), minimum=0),
        FieldSpec('mode', '粘贴方式', 'choice', '全部粘贴', choices=('全部粘贴', '只粘贴值', '只粘贴公式', '只粘贴格式', '保留公式', '值与数字格式', '公式与数字格式', '不覆盖原有内容'), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '复制粘贴（选择性粘贴）'
    COMMAND_ID = 'excelCopyPaste'
