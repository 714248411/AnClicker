from anclicker.ui.instruction_editors.网页抓取工具.Crawl4AI网页抓取 import InstructionEditor as BaseEditor
from anclicker.instructions.网页抓取工具.网页表格提取.schema import FIELDS
from anclicker.instructions.网页抓取工具.网页表格提取.executor import InstructionExecutor
from anclicker.ui.generated.instructions.网页抓取工具.网页表格提取.网页表格提取_ui import Ui_InstructionEditor

class InstructionEditor(BaseEditor):
    TYPE_ID = '网页表格提取'
    DISPLAY_NAME = '网页表格提取'
    FIELDS = FIELDS
    UI_CLASS = Ui_InstructionEditor

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft, context)
        self.preset.clear()
        self.preset.addItem('网页表格提取')
        self._controls['格式'].setCurrentText('表格')
        self._controls['格式'].setEnabled(False)
