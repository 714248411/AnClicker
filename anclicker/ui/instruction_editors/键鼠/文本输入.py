"""文本输入：独立参数编辑器与执行器。"""

from __future__ import annotations
from anclicker.instructions.键鼠.文本输入.schema import FIELDS as InstructionEditor_FIELDS

from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.ui.generated.instructions.键鼠.文本输入.文本输入_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QLabel_QPushButton_QVBoxLayout_QWidget': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QLabel', 'QPushButton', 'QVBoxLayout', 'QWidget'), 0),
    'PasteTextEdit': ('from', 'anclicker.ui.instruction_editors.input_controls', ('PasteTextEdit',), 0),
    'InstructionExecutor': ('from', 'anclicker.instructions.键鼠.文本输入.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "文本输入"
    DISPLAY_NAME = "文本输入"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft, context)
        QLabel, QPushButton, QVBoxLayout, QWidget = _module_imports.load('QLabel_QPushButton_QVBoxLayout_QWidget')
        PasteTextEdit = _module_imports.load('PasteTextEdit')
        original = self._controls['内容']
        holder = QWidget(self)
        layout = QVBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        editor = PasteTextEdit(holder)
        editor.setObjectName(original.objectName())
        editor.setMinimumHeight(100)
        editor.setPlainText(original.toPlainText())
        editor.paste_status = QLabel('', holder)
        editor.paste_status.setWordWrap(True)
        button = QPushButton('粘贴文本', holder)
        button.setAutoDefault(False)
        button.clicked.connect(editor.paste)
        layout.addWidget(editor)
        layout.addWidget(button)
        layout.addWidget(editor.paste_status)
        self.ui.parameterFormLayout.replaceWidget(original, holder)
        original.hide()
        original.deleteLater()
        self._controls['内容'] = editor
        self.ui.parameter_0 = editor


InstructionExecutor = _module_imports.load('InstructionExecutor')
