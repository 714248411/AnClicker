from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.等待页面加载完成_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '等待页面加载完成'
    DISPLAY_NAME = '等待页面加载完成'
    COMMAND_ID = 'waitPageReady'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('timeout', '最长等多久(秒)', 'float', 20, choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '等待页面加载完成'
    COMMAND_ID = 'waitPageReady'
