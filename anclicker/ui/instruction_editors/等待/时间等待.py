"""时间等待：独立参数编辑器与执行器。"""

from __future__ import annotations
from anclicker.instructions.等待.时间等待.schema import FIELDS as InstructionEditor_FIELDS

from datetime import datetime, timedelta
import random
import time
from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.ui.generated.instructions.等待.时间等待.时间等待_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QButtonGroup_QCheckBox_QHBoxLayout_QLabel_QWidget': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QButtonGroup', 'QCheckBox', 'QHBoxLayout', 'QLabel', 'QWidget'), 0),
    'QSignalBlocker': ('from', 'anclicker.platform.qt_compat.QtCore', ('QSignalBlocker',), 0),
    'InstructionExecutor': ('from', 'anclicker.instructions.等待.时间等待.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "时间等待"
    DISPLAY_NAME = "时间等待"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft, context)
        QButtonGroup, QCheckBox, QHBoxLayout, QLabel, QWidget = _module_imports.load('QButtonGroup_QCheckBox_QHBoxLayout_QLabel_QWidget')
        holder = QWidget(self)
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_buttons = {}
        for value, label in (('时间等待', '等待时长'), ('定时等待', '等待到目标时间'), ('随机等待', '随机等待')):
            button = QCheckBox(label, holder)
            self.mode_group.addButton(button)
            self.mode_buttons[value] = button
            button.toggled.connect(lambda checked, mode=value: self._controls['类型'].setCurrentText(mode) if checked else None)
            layout.addWidget(button)
        self.ui.parameterFormLayout.insertRow(0, '等待模式', holder)
        self.ui.parameterFormLayout.setRowVisible(1, False)
        self.mode_hint = QLabel(self)
        self.mode_hint.setWordWrap(True)
        self.ui.parameterFormLayout.addRow(self.mode_hint)
        self._controls['类型'].currentTextChanged.connect(self._update_mode)
        self._update_mode()

    def _update_mode(self, *_):
        QSignalBlocker = _module_imports.load('QSignalBlocker')
        mode = self._controls['类型'].currentText()
        for value, button in self.mode_buttons.items():
            with QSignalBlocker(button):
                button.setChecked(value == mode)
        active = {'时间等待': {'时长', '单位'}, '定时等待': {'时间', '检测频率'},
                  '随机等待': {'最小', '最小单位', '最大', '最大单位'}}[mode]
        for index, field in enumerate(self.FIELDS[1:], 1):
            enabled = field.key in active
            self.ui.parameterFormLayout.setRowVisible(index + 1, enabled)
            self._controls[field.key].setEnabled(enabled)
        hints = {'时间等待': '例如设置 5 秒：执行到本指令 → 等待 5 秒 → 执行下一条。目标时间不参与此模式。',
                 '定时等待': '等待到指定的时钟时间后继续；如果今天的时间已经过去，则等待到明天。',
                 '随机等待': '在最小和最大时长之间随机等待一次，结束后执行下一条。'}
        self.mode_hint.setText(hints[mode])

    def _validate_parameters(self, parameters):
        active = dict(parameters)
        if active.get('类型') != '定时等待':
            active['时间'] = ''
        elif not str(active.get('时间', '')).strip():
            raise ValueError('请选择目标时间，格式为 HH:MM:SS')
        super()._validate_parameters(active)


InstructionExecutor = _module_imports.load('InstructionExecutor')
