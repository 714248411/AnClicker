from anclicker.ui.instruction_editors.background_web import BackgroundWebEditor
from anclicker.instructions.网页后台操作.后台网页点击_可多点_.schema import FIELDS
from anclicker.instructions.网页后台操作.后台网页点击_可多点_.executor import InstructionExecutor
class InstructionEditor(BackgroundWebEditor):
    TYPE_ID = DISPLAY_NAME = '后台网页点击（可多点）'
    COMMAND_ID = 'backgroundClicks'
    FIELDS = FIELDS
