"""Shared variable manager, also used to select instruction output variables."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QAbstractItemView,
    QDialogButtonBox, QMessageBox)
from 数据库操作 import DatabaseOperation


class VariablePool_Win(QDialog):
    def __init__(self, parent=None, database=None, selected_name=''):
        super().__init__(parent)
        self.db = database if database is not None else DatabaseOperation()
        self.selected_name = selected_name
        self.setWindowTitle('设置变量 · 全局变量 / 普通变量')
        self.resize(820, 520)
        self.setMinimumSize(560, 380)
        layout = QVBoxLayout(self)
        tip = QLabel('全局变量：运行后的值自动保存，后续任务可继续使用。\n普通变量：本次任务内共享，下次启动任务时恢复这里设置的初始值。\n双击单元格可修改名称、值和备注；名称必须唯一。')
        tip.setWordWrap(True)
        layout.addWidget(tip)
        actions = QHBoxLayout()
        for text, scope in [('新增普通变量', '普通变量'), ('新增全局变量', '全局变量')]:
            button = QPushButton(text)
            button.clicked.connect(lambda checked=False, value=scope: self.add_row(value))
            actions.addWidget(button)
        remove = QPushButton('删除选中变量')
        remove.clicked.connect(self.delete_row)
        actions.addWidget(remove)
        actions.addStretch()
        layout.addLayout(actions)
        self.tableView = QTableWidget(0, 4)
        self.tableView.setHorizontalHeaderLabels(['变量名称', '作用域', '值 / 初始值', '备注'])
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tableView.horizontalHeader().setMinimumSectionSize(110)
        self.tableView.verticalHeader().setDefaultSectionSize(42)
        layout.addWidget(self.tableView, 1)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText('保存并选择' if selected_name else '保存变量')
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('取消')
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.load_data()

    def load_data(self):
        self.tableView.setRowCount(0)
        for name, remark, value, scope in self.db.get_variable_definitions():
            self._append(name, scope, value, remark)
            if name == self.selected_name:
                self.tableView.selectRow(self.tableView.rowCount()-1)

    def _append(self, name, scope, value='', remark=''):
        row = self.tableView.rowCount()
        self.tableView.insertRow(row)
        for column, text in [(0, name), (2, value), (3, remark)]:
            self.tableView.setItem(row, column, QTableWidgetItem(str(text or '')))
        selector = QComboBox()
        selector.addItems(['普通变量', '全局变量'])
        selector.setCurrentText(scope)
        self.tableView.setCellWidget(row, 1, selector)

    def add_row(self, scope='普通变量'):
        names = {self.tableView.item(row, 0).text() for row in range(self.tableView.rowCount())}
        number = 1
        while f'变量{number}' in names:
            number += 1
        self._append(f'变量{number}', scope)
        row = self.tableView.rowCount()-1
        self.tableView.selectRow(row)
        self.tableView.editItem(self.tableView.item(row, 0))

    def delete_row(self):
        rows = {index.row() for index in self.tableView.selectionModel().selectedRows()}
        for row in sorted(rows, reverse=True):
            self.tableView.removeRow(row)

    def save(self):
        self.tableView.setFocus()
        rows = [(self.tableView.item(row, 0).text(), self.tableView.item(row, 3).text(),
                 self.tableView.item(row, 2).text(), self.tableView.cellWidget(row, 1).currentText())
                for row in range(self.tableView.rowCount())]
        try:
            self.db.save_variable_definitions(rows)
        except Exception as error:
            QMessageBox.warning(self, '变量未保存', str(error))
            return
        row = self.tableView.currentRow()
        if row >= 0:
            self.selected_name = rows[row][0].strip()
        self.accept()
