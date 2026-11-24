"""Log text with one-click, repeatable variable insertion at the caret."""
import re
from anclicker.platform.qt_compat.QtCore import QSignalBlocker
from anclicker.platform.qt_compat.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
    QFormLayout, QPlainTextEdit, QComboBox, QPushButton, QLabel, QDialogButtonBox,
    QSpinBox, QLineEdit)
from anclicker.domain.instruction_interfaces import InstructionEditorInterface
from anclicker.domain.instructions import InstructionDraft
from anclicker.instructions.其他.打印日志.schema import FIELDS


class InstructionEditor(QDialog, InstructionEditorInterface):
    TYPE_ID = DISPLAY_NAME = '打印日志'
    FIELDS = FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent)
        self.context = context
        self.setWindowTitle(self.DISPLAY_NAME)
        self.resize(460, 350)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('日志内容'))
        self.content = QPlainTextEdit()
        self.content.setPlaceholderText('输入要打印的内容，例如：当前进度：{{进度}}')
        self.content.setMinimumHeight(120)
        layout.addWidget(self.content, 1)
        variables = QHBoxLayout()
        variables.addWidget(QLabel('插入变量'))
        self.variable_combo = QComboBox()
        self.variable_combo.setToolTip('每选择一次，在日志内容的光标位置插入一次变量；可重复选择同一变量。')
        variables.addWidget(self.variable_combo, 1)
        self.refresh_button = QPushButton('刷新变量')
        self.refresh_button.setAutoDefault(False)
        self.refresh_button.clicked.connect(self.refresh_variables)
        variables.addWidget(self.refresh_button)
        layout.addLayout(variables)
        hint = QLabel('选择变量后会插入 {{变量名}}，运行时打印变量的当前值。支持多行内容。')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QFormLayout()
        self.repeat = QSpinBox()
        self.repeat.setRange(1, 1000000)
        self.policy = QComboBox()
        self.policy.addItems(['提示异常并暂停', '提示异常并停止', '自动跳过'])
        self.note = QLineEdit()
        form.addRow('重复次数', self.repeat)
        form.addRow('异常处理', self.policy)
        form.addRow('备注', self.note)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('确定')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.variable_combo.activated[int].connect(self.insert_variable)
        self.load_draft(draft or InstructionDraft(self.TYPE_ID))

    def refresh_variables(self, *_):
        names = list(getattr(self.context, 'variables', {}) or {})
        metadata = getattr(self.context, 'metadata', {}) or {}
        database = metadata.get('database')
        getter = getattr(database, 'get_variable_info', None)
        if callable(getter):
            names.extend((getter('dict') or {}).keys())
        hint = metadata.get('condition_hint')
        if callable(hint):
            suggestions = hint() or {}
            names.extend(suggestions.get('target_variables', []))
            names.extend(suggestions.get('candidates', []))
        names.extend(re.findall(r'\{\{([^{}]+)\}\}', self.content.toPlainText()))
        names = list(dict.fromkeys(str(name) for name in names if str(name)))
        with QSignalBlocker(self.variable_combo):
            self.variable_combo.clear()
            self.variable_combo.addItem('请选择变量（选择一次插入一次）', None)
            for name in names:
                self.variable_combo.addItem(name, name)
            self.variable_combo.setCurrentIndex(0)

    def insert_variable(self, index):
        name = self.variable_combo.itemData(index)
        if name is None:
            return
        self.content.insertPlainText('{{' + str(name) + '}}')
        with QSignalBlocker(self.variable_combo):
            self.variable_combo.setCurrentIndex(0)
        self.content.setFocus()

    def load_draft(self, draft):
        draft = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
        self.content.setPlainText(str(draft.parameters.get('内容', '')))
        self.repeat.setValue(draft.repeat_count)
        if self.policy.findText(draft.error_policy) < 0:
            self.policy.addItem(draft.error_policy)
        self.policy.setCurrentText(draft.error_policy)
        self.note.setText(draft.note)
        self.refresh_variables()

    def get_draft(self):
        return InstructionDraft(self.TYPE_ID, {'内容': self.content.toPlainText()},
            repeat_count=self.repeat.value(), error_policy=self.policy.currentText(), note=self.note.text())
