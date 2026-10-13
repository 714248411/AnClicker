from instructions.common import FieldSpec, SchemaInstructionEditor
from instructions.common.background_instruction import BackgroundMethodEditor, BackgroundExecutor, BindingEditor, UnbindingEditor
from importlib import import_module
Ui_InstructionEditor = import_module('.解除后台绑定_ui', __package__).Ui_InstructionEditor

class InstructionEditor(UnbindingEditor):
    TYPE_ID = DISPLAY_NAME = '解除后台绑定'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
    )

class InstructionExecutor(BackgroundExecutor):
    TYPE_ID = '解除后台绑定'
