"""主窗口使用的快捷键说明对话框。"""

from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHeaderView, QTableWidgetItem


class ShortcutTable(QDialog):
    def __init__(self, parent=None, title=None, data=None, width=300):
        super().__init__(parent)
        self.setWindowTitle("快捷键说明")
        self.table = QtWidgets.QTableWidget()
        self.table.setRowCount(12)
        self.table.setColumnCount(2)
        if title:
            self.table.setHorizontalHeaderLabels(title)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        self.button = QtWidgets.QPushButton("我知道了")
        self.button.clicked.connect(self.close)

        if data:
            self.table.setRowCount(len(data))
            for row_, (shortcut_, description_) in enumerate(data):
                shortcut_item_ = QTableWidgetItem(shortcut_)
                shortcut_item_.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                )
                shortcut_item_.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                description_item_ = QTableWidgetItem(description_)
                description_item_.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                )
                description_item_.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_, 0, shortcut_item_)
                self.table.setItem(row_, 1, description_item_)

        layout_ = QtWidgets.QVBoxLayout()
        layout_.addWidget(self.table)
        layout_.addWidget(self.button)
        self.setLayout(layout_)

        table_height_ = self.table.verticalHeader().length()
        self.resize(width, table_height_ + 150)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
