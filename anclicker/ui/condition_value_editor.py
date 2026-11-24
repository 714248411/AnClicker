"""Point-and-click helpers while keeping stored condition values lossless."""
import json
from decimal import Decimal
from anclicker.platform.qt_compat.QtCore import QDateTime, QSignalBlocker
from anclicker.platform.qt_compat.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QDoubleSpinBox, QDateTimeEdit, QFileDialog, QMessageBox,
    QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem, QLabel, QHeaderView)
from anclicker.execution.typed_conditions import sequence, window_titles


class ListValueDialog(QDialog):
    def __init__(self, value, parent=None):
        super().__init__(parent)
        self.setWindowTitle('编辑列表')
        self.resize(430, 330)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('逐项添加内容，选择文本或数字，无需填写括号和逗号。'))
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['类型', '内容'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        line = QHBoxLayout()
        for label, callback in [('添加一项', lambda: self.add_item('')), ('删除选中项', self.remove_items)]:
            button = QPushButton(label)
            button.setAutoDefault(False)
            button.clicked.connect(callback)
            line.addWidget(button)
        layout.addLayout(line)
        self.error = QLabel()
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('确定')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        for item in sequence(value or '[]'):
            self.add_item(item)

    def add_item(self, value):
        row = self.table.rowCount()
        self.table.insertRow(row)
        kind = QComboBox()
        kind.addItems(['文本', '数字', '其他 JSON 值'])
        if isinstance(value, str):
            text = value
        else:
            text = json.dumps(value, ensure_ascii=False)
            kind.setCurrentText('数字' if isinstance(value, (int, float)) and not isinstance(value, bool) else '其他 JSON 值')
        self.table.setCellWidget(row, 0, kind)
        self.table.setItem(row, 1, QTableWidgetItem(text))

    def remove_items(self):
        for row in sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(row)

    def value(self):
        values = []
        for row in range(self.table.rowCount()):
            kind = self.table.cellWidget(row, 0).currentText()
            text = self.table.item(row, 1).text()
            if kind == '文本':
                value = text
            else:
                try:
                    value = json.loads(text)
                    if kind == '数字' and (isinstance(value, bool) or not isinstance(value, (int, float))):
                        raise ValueError()
                    json.dumps(value, allow_nan=False)
                except (ValueError, TypeError):
                    raise ValueError(f'第 {row+1} 项不是有效的{kind}。') from None
            values.append(value)
        return json.dumps(values, ensure_ascii=False, allow_nan=False)

    def accept(self):
        try:
            self.value()
        except ValueError as error:
            self.error.setText(str(error))
            return
        super().accept()


class ConditionValueEditor(QWidget):
    def __init__(self, combo, parent=None):
        super().__init__(parent)
        self.combo = combo
        self.kind = ''
        self.operation = ''
        self.operand = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.mode = QComboBox()
        self.mode.addItems(['直接设置', '变量 / 手动输入'])
        layout.addWidget(self.mode)
        layout.addWidget(combo)
        self.number = QDoubleSpinBox()
        self.number.setDecimals(8)
        self.number.setRange(-1e12, 1e12)
        layout.addWidget(self.number)
        self.date = QDateTimeEdit(QDateTime.currentDateTime())
        self.date.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        self.date.setCalendarPopup(True)
        layout.addWidget(self.date)
        line = QHBoxLayout()
        self.buttons = {}
        for key, label, callback in [('file', '选择文件…', self.pick_file),
            ('folder', '选择目录…', self.pick_folder), ('windows', '选择当前窗口…', self.pick_window),
            ('list', '逐项编辑列表…', self.edit_list), ('today', '今天', self.today)]:
            button = QPushButton(label)
            button.setAutoDefault(False)
            button.clicked.connect(callback)
            self.buttons[key] = button
            line.addWidget(button)
        layout.addLayout(line)
        self.mode.currentIndexChanged.connect(self._mode_changed)
        self.number.valueChanged.connect(self._number_changed)
        self.date.dateTimeChanged.connect(self._date_changed)
        combo.currentTextChanged.connect(self.sync)
        self.configure('', '', False)

    def configure(self, kind, operation, operand):
        self.kind, self.operation, self.operand = kind, operation, operand
        numeric = kind == '数字' or (kind == '列表' and operand and operation.startswith('长度'))
        with QSignalBlocker(self.number):
            self.number.setDecimals(0 if kind == '列表' else 8)
            self.number.setRange(0 if kind == '列表' else -1e12, 1e12)
        self.special = 'number' if numeric else 'date' if kind == '日期' else ''
        placeholders = {'文本': '输入文字，或从下拉框选择变量', '数字': '输入数字或选择变量',
                        '日期': '选择日历时间，或选择日期变量', '列表': '选择列表变量，或点击逐项编辑',
                        '文件目录': '选择文件、目录，或选择路径变量', '窗口存在': '选择当前窗口，或输入标题关键词'}
        self.combo.lineEdit().setPlaceholderText(placeholders.get(kind, ''))
        self.buttons['file'].setVisible(kind == '文件目录' and not operand and operation != '是目录')
        self.buttons['folder'].setVisible(kind == '文件目录' and not operand and operation != '是文件')
        self.buttons['windows'].setVisible(kind == '窗口存在' and not operand)
        self.buttons['list'].setVisible(kind == '列表' and not operand)
        self.buttons['today'].setVisible(kind == '日期')
        self.mode.setVisible(bool(self.special))
        self.sync()

    def sync(self, *_):
        text = self.combo.currentText()
        direct = False
        if self.special == 'number':
            try:
                value = Decimal(text)
                direct = value.is_finite() and Decimal(str(self.number.minimum())) <= value <= Decimal(str(self.number.maximum()))
                direct = direct and value == value.quantize(Decimal(1).scaleb(-self.number.decimals()))
                if direct:
                    with QSignalBlocker(self.number):
                        self.number.setValue(float(value))
            except Exception:
                direct = False
        elif self.special == 'date':
            value = QDateTime.fromString(text, 'yyyy-MM-dd HH:mm:ss')
            if not value.isValid():
                value = QDateTime.fromString(text, 'yyyy-MM-dd')
            direct = value.isValid()
            if direct:
                with QSignalBlocker(self.date):
                    self.date.setDateTime(value)
        with QSignalBlocker(self.mode):
            self.mode.setCurrentIndex(0 if direct else 1)
        self._show_mode()

    def _show_mode(self):
        direct = self.mode.currentIndex() == 0
        self.number.setVisible(self.special == 'number' and direct)
        self.date.setVisible(self.special == 'date' and direct)
        self.combo.setVisible(not self.special or not direct)

    def _mode_changed(self, index):
        if index == 0:
            if self.special == 'number':
                self._number_changed()
            elif self.special == 'date':
                self._date_changed()
        self._show_mode()

    def _number_changed(self, *_):
        if self.special == 'number':
            self.combo.setCurrentText(format(self.number.value(), '.8f').rstrip('0').rstrip('.') or '0')

    def _date_changed(self, *_):
        if self.special == 'date':
            self.combo.setCurrentText(self.date.dateTime().toString('yyyy-MM-dd HH:mm:ss'))

    def today(self):
        self.date.setDateTime(QDateTime.currentDateTime())
        self._date_changed()

    def pick_file(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择要判断的文件')
        if path:
            self.combo.setCurrentText(path)

    def pick_folder(self):
        path = QFileDialog.getExistingDirectory(self, '选择要判断的目录')
        if path:
            self.combo.setCurrentText(path)

    def edit_list(self):
        try:
            dialog = ListValueDialog(self.combo.currentText(), self)
        except ValueError as error:
            QMessageBox.information(self, '编辑列表', str(error) + '\n变量内容在运行时读取；可先填写 [] 新建列表。')
            return
        if dialog.exec() == QDialog.Accepted:
            self.combo.setCurrentText(dialog.value())
        dialog.deleteLater()

    def pick_window(self):
        from anclicker.platform.qt_compat.QtWidgets import QInputDialog
        try:
            titles = sorted(set(title for title in window_titles() if title))
        except Exception as error:
            QMessageBox.warning(self, '读取窗口失败', str(error))
            return
        if not titles:
            QMessageBox.information(self, '选择窗口', '当前没有可选择的窗口，请输入标题关键词。')
            return
        title, ok = QInputDialog.getItem(self, '选择当前窗口', '窗口标题', titles, 0, False)
        if ok:
            self.combo.setCurrentText(title)
