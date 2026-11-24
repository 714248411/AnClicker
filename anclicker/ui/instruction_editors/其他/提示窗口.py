"""提示窗口：独立参数编辑器与执行器。"""

from __future__ import annotations
from anclicker.instructions.其他.提示窗口.schema import FIELDS as InstructionEditor_FIELDS

from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.ui.generated.instructions.其他.提示窗口.提示窗口_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.其他.提示窗口.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "提示窗口"
    DISPLAY_NAME = "提示窗口"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = InstructionEditor_FIELDS

    def _refresh_variables(self, current=''):
        variables = dict(self._variable_database().get_variable_info('dict') or {})
        if self.context is not None:
            variables.update(self.context.variables)
        control = self._controls['变量']
        control.clear()
        control.addItem('')
        control.addItems([str(name) for name in variables if str(name)])
        if current and control.findText(current) < 0:
            control.addItem(current)
        control.setCurrentText(current)

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft, context)
        self._controls['变量'].setToolTip('留空不附加变量；运行时读取选中变量的当前值。')
        self._controls['内容'].setPlaceholderText('可留空只显示变量值；内容与变量直接拼接，可在这里加入空格或换行。')
        self._controls['显示顺序'].setToolTip('控制提示内容与变量值的先后顺序。')



InstructionExecutor = _module_imports.load('InstructionExecutor')
