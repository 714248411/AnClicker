from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.诊断页面（排错）_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '诊断页面（排错）'
    DISPLAY_NAME = '诊断页面(排错)'
    COMMAND_ID = 'diagnosePage'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (

    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '诊断页面（排错）'
    COMMAND_ID = 'diagnosePage'
