from anclicker.instructions.键鼠.多坐标点击.schema import FIELDS as InstructionEditor_FIELDS
"""屏幕多坐标点击：依次执行，支持取点追加和独立随机偏移。"""
import math
import random
import re

from anclicker.platform.qt_compat.QtWidgets import QDialog, QMessageBox
from anclicker.ui.instruction_editors.multi_point_canvas import MultiPointCanvas
from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.ui.generated.instructions.键鼠.多坐标点击.多坐标点击_ui import Ui_InstructionEditor


from anclicker.instructions.键鼠.多坐标点击.executor import parse_points

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.键鼠.多坐标点击.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = '多坐标点击'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._controls['坐标列表'].setMaxLength(2147483647)

    def _validate_parameters(self, parameters):
        super()._validate_parameters(parameters)
        value = str(parameters['坐标列表'])
        if not any(mark in value for mark in ('${', '{{', '☾')):
            parse_points(value)

    def _run_auxiliary(self, key):
        if key != '坐标列表':
            return super()._run_auxiliary(key)
        target = self._controls[key]
        try:
            points = parse_points(target.text()) if target.text().strip() else []
        except ValueError as error:
            QMessageBox.warning(self, '坐标无效', str(error))
            return
        windows = []
        for window in (self.window(), getattr(self, '_workspace_owner', None),
                       self.parentWidget().window() if self.parentWidget() else None):
            if window is not None and window not in [item[0] for item in windows] and window.isVisible():
                windows.append((window, window.windowOpacity()))
        canvas = None
        try:
            for window, opacity in windows: window.setWindowOpacity(0)
            canvas = MultiPointCanvas(points, self)
            if canvas.exec() == QDialog.Accepted:
                target.setText('; '.join(f'{x},{y}' for x, y in canvas.points))
                target.setCursorPosition(len(target.text()))
        finally:
            if canvas is not None: canvas.deleteLater()
            for window, opacity in windows: window.setWindowOpacity(opacity)



InstructionExecutor = _module_imports.load('InstructionExecutor')
