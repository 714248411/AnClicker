"""Standalone migration window; never imports into the user's live database."""
from pathlib import Path
from qt_compat.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                              QFileDialog, QPlainTextEdit)
from openpyxl import load_workbook
from migration_tool import inspect_migration, write_migration_bundle


class MigrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        from info import CURRENT_VERSION, APP_NAME
        self.setWindowTitle(f'{APP_NAME} — 旧版数据迁移工具 {CURRENT_VERSION}')
        self.resize(660, 440)
        layout = QVBoxLayout(self)
        label = QLabel('选择旧版 .xlsx 文件，逐分支转换并生成备份与报告。\n原文件不修改，不运行指令，不替换主程序项目。')
        label.setWordWrap(True)
        layout.addWidget(label)
        self.path = QLineEdit()
        self.path.setPlaceholderText('旧版 .xlsx 文件完整路径')
        layout.addWidget(self.path)
        browse = QPushButton('选择旧版文件')
        browse.clicked.connect(self.browse)
        layout.addWidget(browse)
        self.convert = QPushButton('选择输出文件夹并转换')
        self.convert.clicked.connect(self.run_conversion)
        layout.addWidget(self.convert)
        self.report = QPlainTextEdit()
        self.report.setReadOnly(True)
        layout.addWidget(self.report)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择旧版文件', '', 'Excel (*.xlsx)')
        if path:
            self.path.setText(path)

    def run_conversion(self):
        source = Path(self.path.text().strip().strip('"'))
        if not source.is_file() or source.suffix.lower() != '.xlsx':
            self.report.setPlainText('请选择存在的 .xlsx 文件。')
            return
        output = QFileDialog.getExistingDirectory(self, '选择输出目录', str(source.parent))
        if not output:
            return
        self.convert_file(source, Path(output))

    def convert_file(self, source, output):
        book = plan = None
        self.convert.setEnabled(False)
        try:
            book = load_workbook(source)
            plan = inspect_migration(book, source.parent)
            folder, paths = write_migration_bundle(plan, source, Path(output))
            self.report.setPlainText(
                f'转换 {plan.converted_commands}/{plan.source_commands} 条指令。\n'
                f'输出目录：{folder}\n缺失图片引用：{len(plan.missing_resources)}\n'
                f'未转换分支：{len(plan.errors)}\n'
                '请查看迁移报告，不支持的跳转不会被静默改写。\n' +
                '\n'.join(str(path) for path in paths.values()))
            return folder
        except Exception as error:
            self.report.setPlainText(f'转换失败：{error}\n原文件未修改。')
        finally:
            if plan is not None:
                plan.close()
            if book is not None:
                book.close()
            self.convert.setEnabled(True)
