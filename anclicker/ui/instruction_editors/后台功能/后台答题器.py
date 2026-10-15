from anclicker.instructions.后台功能.后台答题器.schema import FIELDS as PARAMETER_FIELDS
"""Local Word answers. The historical type ID is kept for saved workbooks."""
from anclicker.instructions.common import FieldSpec, SchemaInstructionEditor, InstructionExecutorBase, actions
from anclicker.ui.generated.instructions.后台功能.后台答题器.后台答题器_ui import Ui_InstructionEditor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QLabel': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QLabel',), 0),
    'QFileDialog': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QFileDialog',), 0),
    'InstructionExecutor': ('from', 'anclicker.instructions.后台功能.后台答题器.executor', ('InstructionExecutor',), 0),
})


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = '后台答题器'
    DISPLAY_NAME = '本地Word答题器'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = PARAMETER_FIELDS

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft=draft, context=context)
        QLabel = _module_imports.load('QLabel')
        hint = QLabel('本地读取 .docx 题库，无需后台绑定。支持“题目/答案”两列表格，或“题目：…”与“答案：…”段落。答案保存到变量后供下一步使用。', self)
        hint.setWordWrap(True)
        self.ui.rootLayout.insertWidget(1, hint)

    def _run_auxiliary(self, key):
        if key == '题库路径':
            QFileDialog = _module_imports.load('QFileDialog')
            path, _ = QFileDialog.getOpenFileName(self, '选择本地 Word 题库', '', 'Word 文档 (*.docx)')
            if path:
                self._controls[key].setText(path)
            return
        super()._run_auxiliary(key)

InstructionExecutor = _module_imports.load('InstructionExecutor')
