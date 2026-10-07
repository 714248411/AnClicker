"""One command calls a project without replacing the open workspace."""
from pathlib import Path

from qt_compat.QtCore import QEvent
from qt_compat.QtWidgets import QFileDialog

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor, actions
from .运行项目_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = '运行项目'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (FieldSpec('项目路径', '项目文件', required=True),)

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


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '运行项目'
    CONSUMED_FIELDS = ('项目路径',)

    def execute_once(self, context, command):
        if context.stop_requested:
            return None
        handled, result = actions.delegated(context, self.TYPE_ID, command)
        if handled:
            return result
        runner = context.metadata.get('run_project')
        if runner is None:
            raise RuntimeError('请保存运行项目指令后，在主界面启动或使用单行运行')
        path = actions.substitute_variables(context, str(command.parameters.get('项目路径', '')))
        return runner(path, context)
