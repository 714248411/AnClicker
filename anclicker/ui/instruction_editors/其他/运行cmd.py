"""Native CMD editor with searchable, parameterized command templates."""
import os
from anclicker.ui.path_drop import enable_path_drop
from anclicker.instructions.其他.运行cmd.schema import FIELDS
from anclicker.instructions.其他.运行cmd.executor import InstructionExecutor
from anclicker.instructions.common import SchemaInstructionEditor
from anclicker.ui.generated.instructions.其他.运行cmd.运行cmd_ui import Ui_InstructionEditor
from anclicker.domain.cmd_templates import TEMPLATES, render_template
from anclicker.platform.qt_compat.QtCore import Qt, QSignalBlocker
from anclicker.platform.qt_compat.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QComboBox, QLabel, QPushButton, QWidget, QFileDialog)


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = '运行cmd'
    DISPLAY_NAME = '运行cmd'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        self._template = None
        self._linked = False
        self._writing_command = False
        self._parameters = {}
        super().__init__(parent, draft, context)
        group = QGroupBox('常用命令：选择模板 → 修改参数 → 查看下方命令')
        layout = QVBoxLayout(group)
        self.template_search = QLineEdit()
        self.template_search.setPlaceholderText('搜索：复制、文件夹、ping、下载、Python…')
        layout.addWidget(self.template_search)
        self.template_combo = QComboBox()
        self.template_combo.setMinimumHeight(32)
        self.template_combo.setMaxVisibleItems(16)
        layout.addWidget(self.template_combo)
        self.template_hint = QLabel('选择模板后自动填入命令；也可直接在下方编写 CMD。')
        self.template_hint.setTextFormat(Qt.PlainText)
        self.template_hint.setWordWrap(True)
        layout.addWidget(self.template_hint)
        self.template_form = QFormLayout()
        self.template_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.template_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        layout.addLayout(self.template_form)
        self.apply_template_button = QPushButton('应用参数到命令')
        self.apply_template_button.setMinimumHeight(32)
        self.apply_template_button.setEnabled(False)
        layout.addWidget(self.apply_template_button)
        self.template_status = QLabel('选择模板不会执行命令；测试或运行流程时才执行。')
        self.template_status.setWordWrap(True)
        self.template_status.setTextFormat(Qt.PlainText)
        layout.addWidget(self.template_status)
        self.ui.rootLayout.insertWidget(1, group)
        self.template_search.textChanged.connect(self._filter_templates)
        self.template_combo.activated[int].connect(self._choose_template)
        self.apply_template_button.clicked.connect(self._apply_template)
        self._controls['命令'].textChanged.connect(self._command_edited)
        self._controls['命令'].setMinimumHeight(130)
        self._filter_templates('')
        self.resize(820, min(820, self.screen().availableGeometry().height()-60))

    def _filter_templates(self, text):
        current = self.template_combo.currentData()
        query = text.strip().casefold()
        with QSignalBlocker(self.template_combo):
            self.template_combo.clear()
            self.template_combo.addItem('自定义命令 / 请选择常用模板', None)
            for index, template in enumerate(TEMPLATES):
                if not query or query in ' '.join(template[:4]).casefold():
                    self.template_combo.addItem(template[0] + ' · ' + template[1], index)
            if current is not None:
                self.template_combo.setCurrentIndex(max(0, self.template_combo.findData(current)))

    def _choose_template(self, index):
        template_index = self.template_combo.itemData(index)
        self._parameters = {}
        while self.template_form.rowCount():
            self.template_form.removeRow(0)
        self._template = TEMPLATES[template_index] if template_index is not None else None
        self.apply_template_button.setEnabled(self._template is not None)
        if self._template is None:
            self._linked = False
            self.template_hint.setText('自定义模式：直接编辑下方 CMD 命令。')
            self.template_status.setText('现有命令已保留。')
            return
        self.template_hint.setText(self._template[3])
        for key, label, default, kind in self._template[4]:
            edit = QLineEdit(default)
            edit.setMinimumHeight(32)
            self._parameters[key] = edit
            if kind in ('folder', 'file', 'save'):
                enable_path_drop(edit)
                edit.setToolTip('可直接拖入文件或文件夹填写完整路径')
                holder = QWidget()
                row = QHBoxLayout(holder)
                row.setContentsMargins(0,0,0,0)
                row.addWidget(edit, 1)
                browse = QPushButton('浏览…')
                browse.setMinimumHeight(32)
                browse.clicked.connect(lambda checked=False, key=key, kind=kind: self._browse_parameter(key, kind))
                row.addWidget(browse)
                self.template_form.addRow(label, holder)
            else:
                self.template_form.addRow(label, edit)
            edit.textChanged.connect(self._parameter_changed)
        self._linked = True
        self._apply_template()

    def _browse_parameter(self, key, kind):
        initial = os.path.expandvars(self._parameters[key].text())
        if kind == 'folder':
            path = QFileDialog.getExistingDirectory(self, '选择文件夹', initial)
        elif kind == 'save':
            path, _ = QFileDialog.getSaveFileName(self, '选择保存位置', initial, '所有文件 (*)')
        else:
            path, _ = QFileDialog.getOpenFileName(self, '选择文件', initial, '所有文件 (*)')
        if path:
            self._parameters[key].setText(path)

    def _parameter_changed(self, *_):
        if self._linked:
            self._apply_template()
        else:
            self.template_status.setText('命令已手动修改；点击“应用参数到命令”可重新生成。')

    def _render(self):
        return render_template(self._template, {key: edit.text() for key, edit in self._parameters.items()})

    def _apply_template(self):
        if self._template is None:
            return
        try:
            command = self._render()
        except ValueError as error:
            self.template_status.setText(str(error) + '；命令尚未更新。')
            return
        self._writing_command = True
        try:
            self._controls['命令'].setPlainText(command)
        finally:
            self._writing_command = False
        self._linked = True
        self.template_status.setText('参数已同步到命令。路径已加引号，仍可直接修改下方命令。')

    def _command_edited(self):
        if not self._writing_command:
            self._linked = False
            self.template_status.setText('手动编辑模式；当前保存和执行的是下方命令。')

    def get_draft(self):
        if self._template is not None and self._linked:
            self._render()  # Do not save a stale command while template parameters are invalid.
        return super().get_draft()
