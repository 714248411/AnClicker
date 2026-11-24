"""移动鼠标：独立参数编辑器与执行器。"""

from __future__ import annotations
from anclicker.instructions.键鼠.移动鼠标.schema import FIELDS as InstructionEditor_FIELDS

import random
from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.ui.generated.instructions.键鼠.移动鼠标.移动鼠标_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.键鼠.移动鼠标.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "移动鼠标"
    DISPLAY_NAME = "移动鼠标"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        self._loading_movement = True
        super().__init__(parent=parent, draft=None, context=context)
        from anclicker.platform.qt_compat.QtWidgets import QLineEdit
        old_time = self._controls['持续']
        time_edit = QLineEdit('0.5-1.5', old_time.parentWidget())
        time_edit.setObjectName(old_time.objectName())
        time_edit.setPlaceholderText('0.5-1.5（随机），或输入固定秒数，例如 1')
        time_edit.setToolTip('每次移动在范围内随机取时；输入单个数值则使用固定时间，单位为秒。')
        self.ui.parameterFormLayout.replaceWidget(old_time, time_edit)
        old_time.hide()
        old_time.deleteLater()
        self.ui.parameter_5 = time_edit
        self._controls['持续'] = time_edit
        self.ui.parameterLabel_4.setText('移动目标')
        self.ui.parameterLabel_5.setText('移动时间（秒）')
        # Keep the time row after every possible target control.
        form = self.ui.parameterFormLayout
        for widget in (self.ui.parameterLabel_5, time_edit, self.ui.parameterLabel_6, self.ui.parameterContainer_6):
            form.removeWidget(widget)
        form.setWidget(5, form.LabelRole, self.ui.parameterLabel_6)
        form.setWidget(5, form.FieldRole, self.ui.parameterContainer_6)
        form.setWidget(6, form.LabelRole, self.ui.parameterLabel_5)
        form.setWidget(6, form.FieldRole, time_edit)
        for field in self.FIELDS:
            if field.key in ('类型', '方向'):
                control = self._controls[field.key]
                control.clear()
                control.addItems(field.choices)
                control.setCurrentText(field.default)
        self._controls['类型'].currentTextChanged.connect(self._movement_changed)
        self._controls['方向'].currentTextChanged.connect(self._refresh_fields)
        self._controls['方向'].setToolTip('无：使用目标坐标，由算法自动规划方向；箭头：按方向和距离移动。')
        self._loading_movement = False
        if draft is not None:
            self.load_draft(draft)
        else:
            self._refresh_fields()

    def load_draft(self, draft):
        # Preserve the executor's defaults when opening legacy instructions.
        from anclicker.domain.instructions import InstructionDraft
        draft = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
        self._loading_movement = True
        try:
            mode = draft.parameters.get('类型', '直线移动')
            self._controls['类型'].setCurrentText(mode)
            self._controls['方向'].setCurrentText(
                draft.parameters.get('方向', '无' if mode.startswith('模拟人') else '→'))
            super().load_draft(draft)
        finally:
            self._loading_movement = False
        self._refresh_fields()

    def _validate_parameters(self, parameters):
        super()._validate_parameters(parameters)
        from anclicker.instructions.键鼠.移动鼠标.timing import duration_bounds
        duration_bounds(parameters['持续'])

    def _movement_changed(self, value):
        if self._loading_movement:
            return
        if value.startswith('模拟人'):
            self._controls['方向'].setCurrentText('无')
        elif value == '直线移动' and self._controls['方向'].currentText() == '无':
            self._controls['方向'].setCurrentText('→')
        self._refresh_fields()

    def _refresh_fields(self, *_):
        if self._loading_movement:
            return
        mode = self._controls['类型'].currentText()
        human = mode.startswith('模拟人')
        directed = self._controls['方向'].currentText() != '无'
        visible = {'类型'}
        if mode.startswith('模拟人1'):
            self._controls['方向'].blockSignals(True)
            self._controls['方向'].setCurrentText('无')
            self._controls['方向'].blockSignals(False)
            visible.update(('坐标', '持续'))
        elif human:
            visible.update(('方向', '持续', '距离' if directed else '坐标'))
        elif mode == '直线移动':
            visible.update(('方向', '距离', '持续'))
        elif mode == '随机移动':
            visible.update(('随机', '持续'))
        elif mode == '指定坐标':
            visible.update(('坐标', '持续'))
        elif mode == '变量坐标':
            visible.update(('变量', '持续'))
        for index, field in enumerate(self.FIELDS):
            label = getattr(self.ui, 'parameterLabel_' + str(index))
            widget = getattr(self.ui, 'parameterContainer_' + str(index), self._controls[field.key])
            label.setVisible(field.key in visible)
            widget.setVisible(field.key in visible)


InstructionExecutor = _module_imports.load('InstructionExecutor')
