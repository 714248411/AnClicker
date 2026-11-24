from anclicker.ui.instruction_editors.health_guard import HealthGuardEditor
from anclicker.instructions.本地OCR.多线程血量判断.schema import FIELDS
from anclicker.instructions.本地OCR.多线程血量判断.executor import InstructionExecutor

class InstructionEditor(HealthGuardEditor):
    TYPE_ID = '多线程血量判断'
    DISPLAY_NAME = '多线程血量判断'
    FIELDS = FIELDS
