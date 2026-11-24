from anclicker.ui.instruction_editors.vision_tools import VisionEditor
from anclicker.instructions.本地OCR.字库点击.schema import FIELDS
from anclicker.instructions.本地OCR.字库点击.executor import InstructionExecutor

class InstructionEditor(VisionEditor):
    TYPE_ID = '字库点击'
    DISPLAY_NAME = '字库点击'
    FIELDS = FIELDS
