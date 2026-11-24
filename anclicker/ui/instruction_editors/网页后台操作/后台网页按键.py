from anclicker.ui.instruction_editors.background_web import BackgroundWebEditor
from anclicker.instructions.网页后台操作.后台网页按键.schema import FIELDS
from anclicker.instructions.网页后台操作.后台网页按键.executor import InstructionExecutor
class InstructionEditor(BackgroundWebEditor):
    TYPE_ID = DISPLAY_NAME = '后台网页按键'
    COMMAND_ID = 'backgroundKey'
    FIELDS = FIELDS
