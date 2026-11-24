"""窗口控制：独立参数编辑器与执行器。"""

from __future__ import annotations
from anclicker.instructions.其他.窗口控制.schema import FIELDS as InstructionEditor_FIELDS

import sys

from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord, ExecutionContext, InstructionDraft
from anclicker.ui.generated.instructions.其他.窗口控制.窗口控制_ui import Ui_InstructionEditor as BaseUi

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'pick_background_window': ('from', 'anclicker.ui.background_window_picker', ('pick_background_window',), 0),
    'QMessageBox': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QMessageBox',), 0),
    'InstructionExecutor': ('from', 'anclicker.instructions.其他.窗口控制.executor', ('InstructionExecutor',), 0),
})



from anclicker.platform.qt_compat.QtWidgets import QLabel, QSpinBox, QComboBox

class WindowControlUi(BaseUi):
    def setupUi(self, dialog):
        super().setupUi(dialog)
        self.parameter_1.clear()
        self.parameter_1.addItems(InstructionEditor_FIELDS[1].choices)
        for index, field in enumerate(InstructionEditor_FIELDS[3:], 3):
            label = QLabel(field.label, self.parameterGroupBox)
            if field.kind == 'choice':
                control = QComboBox(self.parameterGroupBox)
                control.addItems(field.choices)
                control.setCurrentText(field.default)
            else:
                control = QSpinBox(self.parameterGroupBox)
                control.setRange(int(field.minimum), int(field.maximum))
                control.setValue(field.default)
            label.setObjectName('parameterLabel_' + str(index))
            control.setObjectName('parameter_' + str(index))
            setattr(self, 'parameterLabel_' + str(index), label)
            setattr(self, 'parameter_' + str(index), control)
            self.parameterFormLayout.insertRow(index - 1, label, control)

class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "窗口控制"
    DISPLAY_NAME = "窗口控制"
    UI_CLASS = WindowControlUi
    FIELDS = InstructionEditor_FIELDS


    def __init__(self, parent=None, draft=None, context=None):
        self._picked_window = {}
        super().__init__(parent=parent,draft=draft,context=context)
        self._controls['操作'].currentTextChanged.connect(self._update_geometry_fields)
        self._controls['移动方式'].currentTextChanged.connect(self._update_geometry_fields)
        self._update_geometry_fields()
        self.ui.pickWindowButton.clicked.connect(self._pick_target_window)
        self._controls['标题包含'].textEdited.connect(self._clear_picked_window)

    def _update_geometry_fields(self, *_):
        operation = self._controls['操作'].currentText()
        move = operation == '窗口移动'
        resize = operation == '窗口大小'
        for index, field in enumerate(self.FIELDS[3:], 3):
            visible = move if field.key in ('移动方式', 'X', 'Y') else resize
            self._controls[field.key].setVisible(visible)
            getattr(self.ui, 'parameterLabel_' + str(index)).setVisible(visible)
        relative = self._controls['移动方式'].currentText() == '相对当前位置'
        self.ui.parameterLabel_4.setText('水平偏移 X（像素）' if relative else '左上角 X（屏幕坐标）')
        self.ui.parameterLabel_5.setText('垂直偏移 Y（像素）' if relative else '左上角 Y（屏幕坐标）')
        self._controls['大小锚点'].setToolTip('调整窗口外框尺寸；固定左上角位置或保持当前窗口中心点不变')

    def _clear_picked_window(self, *_):
        self._picked_window = {}
        self._controls['标题包含'].setToolTip('支持手动输入窗口标题的一部分')

    def _apply_window_selection(self, selected):
        if not selected:
            return False
        title=str(selected.get('窗口标题','')).strip()
        if not title:
            raise ValueError('所选窗口没有标题，请选择应用的主窗口')
        self._picked_window = dict(selected)
        self._controls['标题包含'].setText(title)
        self._controls['标题包含'].setToolTip('已点选窗口：'+title+'\n句柄：'+str(selected.get('窗口句柄',''))+'\n编辑标题后将改为按标题查找')
        return True

    def _pick_target_window(self):
        QMessageBox = _module_imports.load('QMessageBox')
        try:
            pick_background_window = _module_imports.load('pick_background_window')
            self._apply_window_selection(pick_background_window(self))
        except Exception as error:
            QMessageBox.warning(self,'点选窗口未完成',str(error))

    def load_draft(self, draft):
        draft = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
        super().load_draft(draft)
        self._picked_window = dict(draft.parameters.get('窗口定位') or {})
        self._update_geometry_fields()

    def get_draft(self):
        draft=super().get_draft()
        if self._picked_window and draft.parameters.get('标题包含')==self._picked_window.get('窗口标题'):
            draft.parameters['窗口定位']=dict(self._picked_window)
        return draft


InstructionExecutor = _module_imports.load('InstructionExecutor')
