"""暂不运行以上指令：按表格顺序标记注释范围。"""
from qt_compat.QtWidgets import QLabel
from instructions.common import SchemaInstructionEditor, InstructionExecutorBase, actions
from .暂不运行以上指令_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = '暂不运行以上指令'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = ()

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


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '暂不运行以上指令'

    def execute_once(self, context, command):
        delegated, result = actions.delegated(context, self.TYPE_ID, command)
        return result if delegated else None
