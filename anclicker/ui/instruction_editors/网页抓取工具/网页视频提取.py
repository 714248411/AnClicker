from anclicker.ui.instruction_editors.网页抓取工具.Crawl4AI网页抓取 import InstructionEditor as BaseEditor
from anclicker.instructions.网页抓取工具.网页视频提取.schema import FIELDS
from anclicker.instructions.网页抓取工具.网页视频提取.executor import InstructionExecutor
from anclicker.ui.generated.instructions.网页抓取工具.网页图片提取.网页图片提取_ui import Ui_InstructionEditor as BaseUi

class Ui_InstructionEditor(BaseUi):
    def setupUi(self, dialog):
        super().setupUi(dialog)
        self.parameter_1.clear()
        self.parameter_1.addItem('视频')
        self.parameter_6.clear()
        self.parameter_6.addItem('网页视频')
        dialog.setWindowTitle('网页视频提取')
        self.titleLabel.setText('网页视频提取')
        self.parameterGroupBox.setTitle('网页视频提取参数')


class InstructionEditor(BaseEditor):
    TYPE_ID = '网页视频提取'
    DISPLAY_NAME = '网页视频提取'
    FIELDS = FIELDS
    UI_CLASS = Ui_InstructionEditor

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft, context)
        self.preset.clear()
        self.preset.addItem('网页视频提取')
        self._controls['格式'].setCurrentText('视频')
        self._controls['格式'].setEnabled(False)
