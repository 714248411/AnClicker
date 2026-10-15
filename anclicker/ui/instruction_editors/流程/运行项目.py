from anclicker.instructions.流程.运行项目.schema import FIELDS as InstructionEditor_FIELDS
"""One command calls a project without replacing the open workspace."""
from pathlib import Path

from anclicker.platform.qt_compat.QtCore import QEvent
from anclicker.platform.qt_compat.QtWidgets import QFileDialog

from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor, actions
from anclicker.ui.generated.instructions.流程.运行项目.运行项目_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.流程.运行项目.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = '运行项目'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        control = self._controls['项目路径']
        control.setAcceptDrops(True)
        control.installEventFilter(self)
        control.setPlaceholderText('拖入一个 .xlsx 项目，或浏览选择文件')
        # Project execution belongs to the worker, never the modal GUI thread.
        self.test_button.setEnabled(False)
        self.test_button.setToolTip('保存后使用主界面的运行或表格单行运行；可用停止按钮 / Esc 中断')

    def _run_auxiliary(self, key):
        if key == '项目路径':
            path, _ = QFileDialog.getOpenFileName(
                self, '选择要运行的项目', self._controls[key].text(), 'An Clicker 项目 (*.xlsx)')
            if path:
                self._controls[key].setText(path)
            return
        super()._run_auxiliary(key)

    def eventFilter(self, watched, event):
        if watched is self._controls.get('项目路径') and event.type() in (
                QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop):
            urls = event.mimeData().urls()
            valid = (len(urls) == 1 and urls[0].isLocalFile()
                     and Path(urls[0].toLocalFile()).suffix.lower() == '.xlsx'
                     and Path(urls[0].toLocalFile()).is_file())
            if valid:
                if event.type() == QEvent.Type.Drop:
                    watched.setText(urls[0].toLocalFile())
                event.acceptProposedAction()
            else:
                event.ignore()
            return True
        return super().eventFilter(watched, event)


InstructionExecutor = _module_imports.load('InstructionExecutor')
