from anclicker.instructions.流程.暂不运行以下指令.schema import FIELDS as InstructionEditor_FIELDS
"""暂不运行以下指令：按表格顺序标记注释范围。"""
from anclicker.platform.qt_compat.QtWidgets import QLabel
from anclicker.instructions.common import SchemaInstructionEditor, InstructionExecutorBase, actions
from anclicker.ui.generated.instructions.流程.暂不运行以下指令.暂不运行以下指令_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.流程.暂不运行以下指令.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = '暂不运行以下指令'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent=parent, draft=draft, context=context)
        self.ui.parameterGroupBox.hide()
        self.ui.repeatLabel.hide()
        self.ui.repeatSpinBox.hide()
        hint = QLabel('流程图按连线方向，未连接指令按表格顺序：从“暂不运行以下指令”到“暂不运行以上指令”之间不运行。'
                      '单独使用时，跳过以下或以上全部指令。删除标记即可恢复运行。')
        hint.setWordWrap(True)
        self.ui.rootLayout.insertWidget(1, hint)

    def get_draft(self):
        draft = super().get_draft()
        # Comment boundaries are metadata, never repeatable actions.
        draft.repeat_count = 1
        return draft


InstructionExecutor = _module_imports.load('InstructionExecutor')
