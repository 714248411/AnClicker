from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.统计文件（白话）_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '统计文件（白话）'
    DISPLAY_NAME = '统计文件(白话)'
    COMMAND_ID = 'fileCount'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('folder', '统计哪个文件夹', 'text', '', choices=(), minimum=0),
        FieldSpec('ext', '只统计这种类型(如 txt，留空=全部)', 'text', '', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '统计文件（白话）'
    COMMAND_ID = 'fileCount'
