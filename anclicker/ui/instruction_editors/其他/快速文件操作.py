from anclicker.ui.instruction_editors.editor import SchemaInstructionEditor
from anclicker.instructions.其他.快速文件操作.schema import FIELDS
from anclicker.ui.generated.instructions.其他.快速文件操作.快速文件操作_ui import Ui_InstructionEditor
class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID='快速文件操作'
    DISPLAY_NAME='快速文件操作'
    FIELDS=FIELDS
    UI_CLASS=Ui_InstructionEditor
