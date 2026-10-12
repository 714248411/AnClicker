from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.保存Excel_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '保存Excel'
    DISPLAY_NAME = '保存Excel'
    COMMAND_ID = 'excelSave'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('path', '另存为(留空保存原文件)', 'text', '', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '保存Excel'
    COMMAND_ID = 'excelSave'
