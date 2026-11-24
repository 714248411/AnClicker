from anclicker.ui.instruction_editors.vision_tools import VisionEditor
from anclicker.instructions.本地OCR.A星寻路.schema import FIELDS
from anclicker.instructions.本地OCR.A星寻路.executor import InstructionExecutor

class InstructionEditor(VisionEditor):
    TYPE_ID = 'A星寻路'
    DISPLAY_NAME = 'A星寻路'
    FIELDS = FIELDS
