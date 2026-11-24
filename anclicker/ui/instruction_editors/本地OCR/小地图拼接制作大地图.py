from anclicker.ui.instruction_editors.vision_tools import VisionEditor
from anclicker.instructions.本地OCR.小地图拼接制作大地图.schema import FIELDS
from anclicker.instructions.本地OCR.小地图拼接制作大地图.executor import InstructionExecutor

class InstructionEditor(VisionEditor):
    TYPE_ID = '小地图拼接制作大地图'
    DISPLAY_NAME = '小地图拼接制作大地图'
    FIELDS = FIELDS
