from anclicker.instructions.流程.变量比较.schema import FIELDS as InstructionEditor_FIELDS
from anclicker.instructions.common import FieldSpec, InstructionExecutorBase, actions
from anclicker.ui.instruction_editors.flow_jump_editor import JumpEditor
from anclicker.domain.flow_jumps import TARGET_MODES, OPERATORS, compare_variables
from anclicker.ui.generated.instructions.流程.变量比较.变量比较_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QPushButton_QLabel': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QPushButton', 'QLabel'), 0),
    'QCompleter': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QCompleter',), 0),
    'InstructionExecutor': ('from', 'anclicker.instructions.流程.变量比较.executor', ('InstructionExecutor',), 0),
})


class InstructionEditor(JumpEditor):
    TYPE_ID = DISPLAY_NAME = '变量比较'
    UI_CLASS = Ui_InstructionEditor
    PREFIXES = ('是','否')
    FIELDS = InstructionEditor_FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent=parent, draft=draft, context=context)
        QPushButton, QLabel = _module_imports.load('QPushButton_QLabel')
        self.infer_condition_button = QPushButton('根据前后指令填入变量', self)
        self.infer_condition_button.setAutoDefault(False)
        self.condition_hint_label = QLabel(self)
        self.condition_hint_label.setWordWrap(True)
        self.ui.parameterFormLayout.insertRow(1, self.infer_condition_button)
        self.ui.parameterFormLayout.insertRow(2, self.condition_hint_label)
        self._condition_hint_callback = getattr(context, 'metadata', {}).get('condition_hint')
        self.infer_condition_button.clicked.connect(lambda: self._infer_condition(replace=True))
        self._infer_condition(replace=draft is None)

    def _infer_condition(self, replace=False):
        if self._condition_hint_callback is None:
            self.condition_hint_label.setText('可手动指定变量；连接前后指令后可自动推断。')
            return
        try:
            hint = self._condition_hint_callback()
        except Exception as error:
            self.condition_hint_label.setText('无法读取相邻指令：' + str(error))
            return
        QCompleter = _module_imports.load('QCompleter')
        self._controls['变量'].setCompleter(QCompleter(hint['candidates'], self))
        variable = hint['variable']
        self.condition_hint_label.setText('建议变量：' + variable if variable else
            '请手动选择变量：' + ('、'.join(hint['candidates']) or '前后指令没有可确定的变量'))
        if replace and variable:
            self._controls['变量'].setCurrentText(variable)

InstructionExecutor = _module_imports.load('InstructionExecutor')
