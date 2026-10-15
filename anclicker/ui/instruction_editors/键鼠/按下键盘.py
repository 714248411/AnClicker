"""按下键盘：独立参数编辑器与执行器。"""

from __future__ import annotations
from anclicker.instructions.键鼠.按下键盘.schema import FIELDS as InstructionEditor_FIELDS

from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.ui.generated.instructions.键鼠.按下键盘.按下键盘_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QComboBox_QHBoxLayout_QPushButton_QWidget': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QComboBox', 'QHBoxLayout', 'QPushButton', 'QWidget'), 0),
    'QDialog_QMessageBox': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QDialog', 'QMessageBox'), 0),
    'KeyCaptureDialog': ('from', 'anclicker.ui.instruction_editors.input_controls', ('KeyCaptureDialog',), 0),
    'InstructionExecutor': ('from', 'anclicker.instructions.键鼠.按下键盘.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "按下键盘"
    DISPLAY_NAME = "按下键盘"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft, context)
        QComboBox, QHBoxLayout, QPushButton, QWidget = _module_imports.load('QComboBox_QHBoxLayout_QPushButton_QWidget')
        form = self.ui.parameterFormLayout
        keys = self._controls['按键']
        duration = self._controls['按压时长']
        for row, control in ((0, keys), (1, duration)):
            form.removeWidget(control)
            holder = QWidget(self)
            layout = QHBoxLayout(holder)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(control, 1)
            if row == 0:
                self.capture_button = QPushButton('捕获按键', holder)
                self.capture_button.setAutoDefault(False)
                self.capture_button.clicked.connect(self.capture_keys)
                layout.addWidget(self.capture_button)
            else:
                self.duration_presets = QComboBox(holder)
                self.duration_presets.addItem('常用时长（毫秒）', None)
                for value in (5, 10, 20, 30, 50, 100, 200, 500, 1000, 2000, 5000):
                    self.duration_presets.addItem(str(value), value)
                self.duration_presets.activated.connect(self.apply_duration_preset)
                layout.addWidget(self.duration_presets)
            form.setWidget(row, form.ItemRole.FieldRole, holder)

    def apply_duration_preset(self, index):
        value = self.duration_presets.itemData(index)
        if value is not None:
            self._controls['按压时长'].setValue(value)

    def capture_keys(self):
        QDialog, QMessageBox = _module_imports.load('QDialog_QMessageBox')
        KeyCaptureDialog = _module_imports.load('KeyCaptureDialog')
        owner = self.parentWidget()
        while owner is not None and not hasattr(owner, 'unregister_global_shortcut_keys'):
            owner = owner.parentWidget()
        if owner is not None and owner.command_thread.isRunning():
            QMessageBox.information(self, '请先停止任务', '运行时不能捕获按键，请先停止任务。')
            return
        dialog = KeyCaptureDialog(self)
        try:
            if owner is not None:
                owner.unregister_global_shortcut_keys()
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.value:
                self._controls['按键'].setText(dialog.value)
        finally:
            dialog.deleteLater()
            if owner is not None:
                owner.register_global_shortcut_keys()


InstructionExecutor = _module_imports.load('InstructionExecutor')
