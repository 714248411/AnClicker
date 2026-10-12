from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.等待（秒）_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '等待（秒）'
    DISPLAY_NAME = '等待(秒)'
    COMMAND_ID = 'browserWait'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('seconds', '等待时间(秒)', 'float', 1, choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '等待（秒）'
    COMMAND_ID = 'browserWait'
