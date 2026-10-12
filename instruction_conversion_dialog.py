"""Review missing instruction content before committing conversion."""
from qt_compat.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QPlainTextEdit


class InstructionConversionDialog(QDialog):
    def __init__(self, plan, parent=None):
        super().__init__(parent)
        self.setWindowTitle('写入表格与流程图 · 检查补充内容')
        self.resize(780, 440)
        layout = QVBoxLayout(self)
        buttons = QHBoxLayout()
        self.convert_button = QPushButton('继续转换')
        self.convert_button.setObjectName('accentButton')
        self.cancel_button = QPushButton('不转换')
        buttons.addWidget(self.convert_button)
        buttons.addWidget(self.cancel_button)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.convert_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.convert_button.setEnabled(bool(plan.entries) and not plan.errors)
        self.cancel_button.setDefault(True)
        tip = QLabel('继续转换后补齐默认参数并写入。无法推断的目标标记待补充、运行时跳过；可在表格修改后恢复执行。')
        tip.setWordWrap(True)
        layout.addWidget(tip)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        lines = plan.errors + plan.notices
        if not lines:
            lines = ['检查完成：没有需要补充的内容，可以继续转换。']
        if plan.errors:
            lines.insert(0, '以下内容无法确定默认值，请选择“不转换”后按位置修改。')
        self.details.setPlainText('\n\n'.join(lines))
        layout.addWidget(self.details, 1)
