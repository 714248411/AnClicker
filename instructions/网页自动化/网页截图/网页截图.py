from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.网页截图_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '网页截图'
    DISPLAY_NAME = '网页截图'
    COMMAND_ID = 'screenshot'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('selector', '元素定位(可选)', 'text', '', choices=(), minimum=0),
        FieldSpec('path', '保存路径', 'text', '', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '网页截图'
    COMMAND_ID = 'screenshot'
