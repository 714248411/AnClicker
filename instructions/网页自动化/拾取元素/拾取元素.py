from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.拾取元素_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '拾取元素'
    DISPLAY_NAME = '拾取元素'
    COMMAND_ID = 'pickElement'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('hint', '说明', 'text', '在浏览器里点击目标元素', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '拾取元素'
    COMMAND_ID = 'pickElement'
