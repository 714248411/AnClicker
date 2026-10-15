"""图像等待：独立参数编辑器与执行器。"""

from __future__ import annotations
from anclicker.instructions.等待.图像等待.schema import FIELDS as InstructionEditor_FIELDS

import time
import math
import os
from dataclasses import replace
from anclicker.platform.qt_compat.QtWidgets import QMessageBox
from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord, ExecutionContext, InstructionDraft
from anclicker.execution.instruction_helpers.image_wait import normalize_image_wait
from anclicker.ui.generated.instructions.等待.图像等待.图像等待_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.等待.图像等待.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "图像等待"
    DISPLAY_NAME = "图像等待"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._controls['等待类型'].setToolTip('兼容旧版：等待到指定图像出现 / 等待到指定图像消失')
        self._controls['超时时间'].setSpecialValueText('不限（可停止）')

    def load_draft(self, draft):
        if not isinstance(draft, InstructionDraft):
            draft = InstructionDraft.from_mapping(draft)
        super().load_draft(replace(draft, parameters=normalize_image_wait(draft.parameters)))

    def _test_if_valid(self):
        # The shared editor test handler runs on the GUI thread. Never start
        # an unlimited wait there; the ordinary worker has stop/Esc handling.
        if self._controls['超时时间'].value() == 0:
            QMessageBox.information(self, '不限时等待测试',
                                    '请保存指令后使用表格单行运行测试，可用停止按钮或 Esc 中断。')
            return
        super()._test_if_valid()


InstructionExecutor = _module_imports.load('InstructionExecutor')
