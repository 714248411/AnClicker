from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.坐标点击（可多点）_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '坐标点击（可多点）'
    DISPLAY_NAME = '坐标点击(可多点)'
    COMMAND_ID = 'clickXY'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('points', '点击坐标(最多9个点，用;分隔，如 100,200; 300,400)', 'text', '', choices=(), minimum=0),
        FieldSpec('interval', '每个点之间间隔(秒)', 'float', 1, choices=(), minimum=0),
        FieldSpec('clickType', '点击方式', 'choice', '单击', choices=('单击', '双击', '右键'), minimum=0),
        FieldSpec('x', 'X坐标(只在单点、且上面没填时用)', 'float', 0, choices=(), minimum=0),
        FieldSpec('y', 'Y坐标(只在单点、且上面没填时用)', 'float', 0, choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '坐标点击（可多点）'
    COMMAND_ID = 'clickXY'
