"""Screen pixel comparison with explicit yes/no flow branches."""
from __future__ import annotations
from anclicker.instructions.键鼠.颜色判断.schema import FIELDS as InstructionEditor_FIELDS

import re
from anclicker.platform.qt_compat.QtCore import Qt, QTimer
from anclicker.platform.qt_compat.QtGui import QColor
from anclicker.platform.qt_compat.QtWidgets import QColorDialog, QLabel
from anclicker.ui.instruction_editors.editor import _PointSelectionDialog
from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor, actions
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.ui.generated.instructions.键鼠.颜色判断.颜色判断_ui import Ui_InstructionEditor


from anclicker.instructions.键鼠.颜色判断.executor import rgb

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.键鼠.颜色判断.executor', ('InstructionExecutor',), 0),
})



class ColorPointSelectionDialog(_PointSelectionDialog):
    """Read a pixel only after the selection overlay is transparent."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = None
        self._sampling = False
        self.sample_timer = QTimer(self)
        self.sample_timer.setSingleShot(True)
        self.sample_timer.timeout.connect(self._sample_color)
        self.findChild(QLabel).setText('左键点选位置并获取颜色（不会点击底层窗口） · Esc 取消')

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self._sampling:
            return
        try:
            position = actions.pyautogui_module().position()
            self.point = (int(position.x), int(position.y))
            self._sampling = True
            # Keep exec() alive while allowing the compositor to remove the tint.
            self.setWindowOpacity(0)
            self.sample_timer.start(80)
        except Exception as error:
            self.capture_error = str(error)
            self.reject()

    def _sample_color(self):
        if not self.isVisible():
            return
        try:
            self.color = rgb(actions.pyautogui_module().pixel(*self.point))
            self.accept()
        except Exception as error:
            self.capture_error = str(error)
            self.reject()

    def reject(self):
        self.sample_timer.stop()
        super().reject()


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = '颜色判断'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft, context)
        self.ui.auxiliary_0.setText('获取坐标和颜色')
        self.ui.auxiliary_0.setToolTip('点选屏幕位置，同时填写检测坐标和该位置的颜色；之后可手动修改。')
        self.ui.auxiliary_1.setToolTip('只修改目标颜色，保留当前检测坐标。')
        self._controls['坐标'].setPlaceholderText('x,y；可手动修改')
        self._controls['颜色'].setPlaceholderText('#RRGGBB 或 R,G,B；可手动修改')

    def _create_point_selector(self, key_):
        return ColorPointSelectionDialog(self) if key_ == '坐标' else super()._create_point_selector(key_)

    def _apply_point_selection(self, key_, control_, selector_):
        color = QColor(*selector_.color).name().upper()
        super()._apply_point_selection(key_, control_, selector_)
        self._controls['颜色'].setText(color)

    def _validate_parameters(self, parameters_):
        super()._validate_parameters(parameters_)
        rgb(parameters_['颜色'])

    def _run_auxiliary(self, key_):
        if key_ == '颜色':
            try:
                initial = QColor(*rgb(self._controls[key_].text()))
            except ValueError:
                initial = QColor('#ffffff')
            color = QColorDialog.getColor(initial, self, '选择目标颜色')
            if color.isValid():
                self._controls[key_].setText(color.name().upper())
            return
        super()._run_auxiliary(key_)


InstructionExecutor = _module_imports.load('InstructionExecutor')
