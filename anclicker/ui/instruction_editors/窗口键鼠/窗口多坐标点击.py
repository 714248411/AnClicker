from anclicker.ui.instruction_editors.窗口键鼠.窗口键鼠 import InstructionEditor as BaseEditor
from anclicker.instructions.窗口键鼠.窗口多坐标点击.schema import FIELDS, OPERATIONS
from anclicker.instructions.窗口键鼠.窗口多坐标点击.executor import validate_points
from anclicker.domain.instructions import InstructionDraft
from anclicker.platform.qt_compat.QtWidgets import (QTableWidget, QTableWidgetItem, QAbstractItemView,
    QHeaderView, QGridLayout, QPushButton, QDoubleSpinBox, QLabel, QMessageBox)


class InstructionEditor(BaseEditor):
    TYPE_ID = DISPLAY_NAME = '窗口多坐标点击'
    FIELDS = FIELDS
    OPERATIONS = OPERATIONS

    def __init__(self, parent=None, draft=None, context=None):
        self.pending_draft = draft
        super().__init__(parent, draft=None, context=context)
        self.pick_start.setText('点选并添加坐标')
        toolbar = QGridLayout()
        button_index = 0
        for title, callback in [('添加当前坐标', self.add_current), ('删除选中', self.remove_rows),
                                ('上移', lambda: self.move_row(-1)), ('下移', lambda: self.move_row(1))]:
            button = QPushButton(title)
            button.setAutoDefault(False)
            button.clicked.connect(callback)
            toolbar.addWidget(button, button_index // 2, button_index % 2)
            button_index += 1
        self.interval = QDoubleSpinBox()
        self.interval.setRange(0, 3600)
        self.interval.setDecimals(3)
        self.interval.setValue(0.2)
        self.interval.setSuffix(' 秒')
        toolbar.addWidget(QLabel('点击间隔:'), 2, 0)
        toolbar.addWidget(self.interval, 2, 1)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['相对 X', '相对 Y'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setMinimumHeight(180)
        self.layout().insertLayout(3, toolbar)
        self.layout().insertWidget(4, self.table, 1)
        self.resize(660, 620)
        self.load_draft(draft or InstructionDraft(self.TYPE_ID))

    def add_point(self, x, y):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(x)))
        self.table.setItem(row, 1, QTableWidgetItem(str(y)))
        self.table.selectRow(row)

    def add_current(self):
        self.add_point(self.fields['X'].value(), self.fields['Y'].value())

    def point_selected(self, x, y, end):
        self.add_point(x, y)

    def remove_rows(self):
        for row in sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(row)

    def move_row(self, direction):
        row = self.table.currentRow()
        other = row + direction
        if row < 0 or not 0 <= other < self.table.rowCount():
            return
        for column in range(2):
            a, b = self.table.takeItem(row, column), self.table.takeItem(other, column)
            self.table.setItem(row, column, b)
            self.table.setItem(other, column, a)
        self.table.selectRow(other)

    def load_draft(self, draft):
        super().load_draft(draft)
        if not hasattr(self, 'table'):
            return
        draft = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
        self.table.setRowCount(0)
        for x, y in draft.parameters.get('坐标列表', []):
            self.add_point(x, y)
        self.interval.setValue(float(draft.parameters.get('间隔', 0.2)))

    def get_draft(self):
        draft = super().get_draft()
        try:
            points = [[int(self.table.item(row, col).text()) for col in range(2)]
                      for row in range(self.table.rowCount())]
        except (ValueError, AttributeError):
            raise ValueError('请在坐标列表中填写整数 X、Y')
        draft.parameters.pop('X', None)
        draft.parameters.pop('Y', None)
        draft.parameters.update({'坐标列表': points, '间隔': self.interval.value()})
        validate_points(draft.parameters)
        return draft

    def accept(self):
        try:
            self.get_draft()
        except ValueError as error:
            QMessageBox.warning(self, self.DISPLAY_NAME, str(error))
            return
        super().accept()
