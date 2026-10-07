"""文本输入：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .文本输入_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "文本输入"
    DISPLAY_NAME = "文本输入"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("内容", "输入内容", "multiline", "", required=True),
        FieldSpec("手动输入", "特殊控件手动输入", "bool", False),
    )

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft, context)
        from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
        from instructions.common.input_controls import PasteTextEdit
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


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "文本输入"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"文本输入执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        text_ = actions.substitute_variables(context, str(actions.parameter(command.parameters, "内容", "文本", default="")))
        gui_ = actions.pyautogui_module()
        if actions.parameter(command.parameters, "手动输入", default=False):
            gui_.write(text_)
        else:
            import pyperclip
            pyperclip.copy(text_)
            gui_.hotkey("ctrl", "v")
        context.emit(f"文本输入：{text_}")
        return text_
