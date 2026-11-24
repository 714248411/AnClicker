from anclicker.ui.instruction_editors.editor import SchemaInstructionEditor
from anclicker.instructions.本地OCR.截图OCR核验.schema import FIELDS
from anclicker.ui.generated.instructions.本地OCR.截图OCR核验.截图OCR核验_ui import Ui_InstructionEditor
class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID='截图OCR核验'
    DISPLAY_NAME='截图OCR核验'
    FIELDS=FIELDS
    UI_CLASS=Ui_InstructionEditor
