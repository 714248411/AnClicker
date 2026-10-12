from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.查找文件（白话）_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '查找文件（白话）'
    DISPLAY_NAME = '查找文件(白话)'
    COMMAND_ID = 'fileFind'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('folder', '在哪个文件夹找', 'text', '', choices=(), minimum=0),
        FieldSpec('keyword', '文件名包含什么字(留空=列出全部)', 'text', '', choices=(), minimum=0),
        FieldSpec('ext', '只找这种类型(如 txt，留空=全部)', 'text', '', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '查找文件（白话）'
    COMMAND_ID = 'fileFind'
